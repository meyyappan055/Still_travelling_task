import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transcript import get_transcript
import asyncio
import httpx

current_dir = os.path.dirname(os.path.realpath(__file__))
dotenv_path = os.path.join(current_dir, '..', '.env')

load_dotenv(dotenv_path=dotenv_path)

API_KEY = os.getenv("YOUTUBE_API_KEY")

app = FastAPI()
youtube = build('youtube', 'v3', developerKey=API_KEY)


class VideoRequest(BaseModel):
    search_query: str
    no_of_results: int


async def get_video_details(video_id: str):
    stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={API_KEY}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(stats_url)
            response.raise_for_status()
            stats_data = response.json().get("items", [])[0].get("statistics", {})
            view_count = stats_data.get("viewCount", 0)
            comment_count = stats_data.get("commentCount", 0)
            return view_count, comment_count
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error in getting video details: {e}")


async def get_video_transcript(video_id: str):
    try : 
        transcript = get_transcript(video_id)
        return {"transcript": transcript, "has_transcript": True}
    
    except Exception as e:
        return {"transcript": f"error occured in fetching: {e}","has_transcript": False}


async def get_video_duration(video_id: str):
    details_url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id={video_id}&key={API_KEY}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(details_url)
            response.raise_for_status()
            return response.json().get("items", [])[0].get("contentDetails", {}).get("duration", "")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error in getting video duration: {e}")


async def get_video_category_name(video_id: str):
    video_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={API_KEY}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(video_url)
            response.raise_for_status()
            category_id = response.json().get("items", [])[0].get("snippet", {}).get("categoryId", "")

            category_url = f"https://www.googleapis.com/youtube/v3/videoCategories?part=snippet&id={category_id}&key={API_KEY}"
            category_response = await client.get(category_url)
            category_response.raise_for_status()
            return category_response.json().get("items", [])[0].get("snippet", {}).get("title", "")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error in getting video category: {e}")


def extract_tags_from_description(description: str):
    tags_in_desc = []
    formatted_desc = description.split(" ")
    for word in formatted_desc:
        if "#" in word:
            tags_in_desc.append(word.strip())

    return tags_in_desc


async def fetch_location(video_id: str):
    details_url = f"https://www.googleapis.com/youtube/v3/videos?part=recordingDetails&id={video_id}&key={API_KEY}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(details_url)
            response.raise_for_status()
            recording_details = response.json().get("items", [])[0].get("recordingDetails", {})
            location = recording_details.get("location", "location not mentioned")
            return location
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error in getting video location: {e}")


async def fetch_video_data(res, each, search_query):
    try:
        video_id = res['items'][each]['id'].get('videoId', None)
        if not video_id:
            raise ValueError("videoId is missing in the response.")
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        snippet = res["items"][each]["snippet"]
        title = snippet.get("title", "No Title")
        desc = snippet.get("description", "No Description")
        channelTitle = snippet.get("channelTitle", "No Channel Title")
        tags_in_desc = extract_tags_from_description(desc)
        tags = snippet.get("tags", []) + tags_in_desc
        topic = search_query
        publishedAt = snippet.get("publishedAt", "Unknown Date")

        video_details, duration, category_name, transcript_data, location = await asyncio.gather(
            get_video_details(video_id),
            get_video_duration(video_id),
            get_video_category_name(video_id),
            get_video_transcript(video_id),
            fetch_location(video_id)
        )

        view_count, comment_count = video_details

        return [
            video_url, title, desc, channelTitle, tags, topic, publishedAt,
            view_count, comment_count, duration, category_name, transcript_data, location
        ]

    except Exception as e:
        return f"Error processing video {each}: {e}"
        


def save_to_csv(data):
    columns = [
        "Video_url",
        "Title",
        "Description",
        "Channel Title",
        "Tags",
        "Topic",
        "Published at",
        "Views Counts",
        "Comment Counts",
        "Duration",
        "Category Name",
        "Transcript",
        "Location"
    ]

    try:    
        df = pd.DataFrame(data,columns=columns)
        df.to_csv("video_data.csv",index=False)

    except Exception as e:
        return f"Error in saving to csv: {e}"


@app.post("/get_videos")
async def get_videos(request: VideoRequest):
    try:
        search_query = request.search_query
        no_of_results = request.no_of_results

        next_page_token = None
        data = []

        while len(data) < no_of_results:
            max_results = min(50, no_of_results - len(data))  
            res = youtube.search().list(
                part="snippet",
                q=search_query,
                type="video",
                maxResults=max_results,
                pageToken=next_page_token  
            ).execute()

            tasks = []

            for each in range(len(res["items"])):
                tasks.append(fetch_video_data(res, each, search_query))
            
            results = await asyncio.gather(*tasks,return_exceptions=True)
                
            for result in results:
                if isinstance(result,Exception):
                    data.append([f"Error processing video: {result}"])
                else:
                    data.append(result)


            next_page_token = res.get('nextPageToken') 
            if not next_page_token: 
                break

        save_to_csv(data)

        return {"data": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in fetching YouTube search results: {e}")

