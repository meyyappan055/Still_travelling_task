import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from transcript import get_transcript

current_dir = os.path.dirname(os.path.realpath(__file__))
dotenv_path = os.path.join(current_dir, '..', '.env')

load_dotenv(dotenv_path=dotenv_path)

API_KEY = os.getenv("YOUTUBE_API_KEY")

app = FastAPI()
youtube = build('youtube', 'v3', developerKey=API_KEY)


class VideoRequest(BaseModel):
    search_query: str
    no_of_results: int


def get_video_details(video_id: str):
    try:
        stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={API_KEY}"
        response = requests.get(stats_url)
        response.raise_for_status()
        stats_data = response.json().get("items", [])[0].get("statistics", {})
        view_count = stats_data.get("viewCount", 0)
        comment_count = stats_data.get("commentCount", 0)
        return view_count, comment_count
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in getting video details: {e}")


def get_video_transcript(video_id: str):
    try : 
        transcript = get_transcript(video_id)
        return {"transcript": transcript, "has_transcript": True}
    
    except Exception as e:
        return {"transcript": f"error occured in fetching: {e}","has_transctipt": False}


def get_video_duration(video_id: str):
    try:
        details_url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id={video_id}&key={API_KEY}"
        response = requests.get(details_url)
        response.raise_for_status()
        return response.json().get("items", [])[0].get("contentDetails", {}).get("duration", "")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in getting video duration: {e}")


def get_video_category_name(video_id: str):
    try:
        video_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={API_KEY}"
        response = requests.get(video_url)
        response.raise_for_status()
        category_id = response.json().get("items", [])[0].get("snippet", {}).get("categoryId", "")
        
        category_url = f"https://www.googleapis.com/youtube/v3/videoCategories?part=snippet&id={category_id}&key={API_KEY}"
        category_response = requests.get(category_url)
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


def fetch_video_data(res, each, search_query):
    try:
        video_id = res['items'][each]['id']['videoId']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        title = res["items"][each]["snippet"]["title"]
        desc = res["items"][each]["snippet"]["description"]
        channelTitle = res["items"][each]["snippet"]["channelTitle"]
        tags_in_desc = extract_tags_from_description(desc)
        tags = res["items"][each]["snippet"].get("tags", [])
        tags += tags_in_desc
        topic = search_query
        publishedAt = res["items"][each]["snippet"]["publishedAt"]
        view_count, comment_count = get_video_details(video_id)
        duration = get_video_duration(video_id)
        category_name = get_video_category_name(video_id)
        transcript_data = get_transcript(video_id)

        return [video_url, title, desc, channelTitle, tags, topic, publishedAt, view_count, comment_count, duration, category_name,  transcript_data]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in processing video data: {e}")


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
        "Transcript"
    ]
    df = pd.DataFrame(data,columns=columns)
    df.to_csv("video_data.csv",index=False)


@app.post("/get_videos")
async def get_videos(request: VideoRequest):
    try:
        search_query = request.search_query
        no_of_results = request.no_of_results
        res = youtube.search().list(
            part="snippet",
            q=search_query,
            type="video",
            maxResults=no_of_results
        ).execute()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in fetching YouTube search results: {e}")

    data = []
    for each in range(no_of_results):
        try:
            video_data = fetch_video_data(res, each, search_query)
            data.append(video_data)
        except HTTPException as e:
            raise e  

    save_to_csv(data)

    return {"data": data}
