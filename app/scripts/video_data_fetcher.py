import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from fastapi import FastAPI
from pydantic import BaseModel
import requests

load_dotenv()
API_KEY = os.getenv("API_KEY")

app = FastAPI()
youtube = build('youtube','v3',developerKey= API_KEY)


class VideoRequest(BaseModel):
    search_query: str
    no_of_results: int


@app.post("/get_videos")
async def get_videos(request: VideoRequest):
    search_query = request.search_query
    no_of_results = request.no_of_results

    res = youtube.search().list(
        part="snippet",
        q = search_query,
        type="video",
        maxResults = no_of_results
    ).execute()

    data =[]
    for each in range(no_of_results):

        videourl = f"https://www.youtube.com/watch?v={res['items'][each]['id']['videoId']}"
        video_id = res['items'][each]['id']['videoId']
        title = res["items"][each]["snippet"]["title"]
        desc = res["items"][each]["snippet"]["description"]
        channelTitle = res["items"][each]["snippet"]["channelTitle"]

        tags_in_desc = []
        formatted_desc = desc.split(" ")
        for word in range(formatted_desc):
            if "#" in word:
                tags_in_desc.append(word.strip())

        tags = res["items"][each]["snippet"].get("tags", []) #empty if no tag is there
        tags += tags_in_desc

        topic = search_query
        publishedAt = res["items"][each]["snippet"]["publishedAt"]
        

        stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={API_KEY}"
        response = requests.get(stats_url)
        stats_data = response.json()["items"][0]["statistics"]
        view_count = stats_data["viewCount"]
        comment_count = stats_data.get("commentCount", 0) #default = 0


        details_url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id={video_id}&key={API_KEY}"
        response = requests.get(details_url)
        duration = response.json()["items"][0]["contentDetails"]["duration"]


        #get category id of the video
        video_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={API_KEY}"
        video_response = requests.get(video_url)
        category_id = video_response.json()["items"][0]["snippet"]["categoryId"]

        
        #category name from category id
        category_url = f"https://www.googleapis.com/youtube/v3/videoCategories?part=snippet&id={category_id}&key={API_KEY}"
        category_response = requests.get(category_url)
        category_name = category_response.json()["items"][0]["snippet"]["title"]

        content = [videourl, title, desc, channelTitle, topic, publishedAt,tags , view_count, duration, category_name , comment_count]
        

        data.append(content)

    return {"data": data}

