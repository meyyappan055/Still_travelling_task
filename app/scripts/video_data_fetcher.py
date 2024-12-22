import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from fastapi import FastAPI
from pydantic import BaseModel

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
        title = res["items"][each]["snippet"]["title"]
        desc = res["items"][each]["snippet"]["description"]
        channelTitle = res["items"][each]["snippet"]["channelTitle"]
        topic = search_query
        publishedAt = res["items"][each]["snippet"]["publishedAt"]
        content = [videourl, title, desc, channelTitle, topic, publishedAt]
        data.append(content)

    return {"data": data}

