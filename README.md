# YouTube Data Fetcher

A FastAPI-based application for analyzing video data from YouTube. This app retrieves video details, including title, description, views, comments, tags, category, transcript, and more, and saves the data to a CSV file.

---

## Features

- Search for videos using a query (search content).
- Fetch video statistics (views, comments, etc.).
- Extract video transcripts (if available).
- Retrieve video duration and category.
- Identify hashtags in video descriptions.
- Fetch recording location details (if available).
- Save all video data to a CSV file.

---

## Requirements

- Python
- `googleapiclient`
- `fastapi`
- `pandas`
- `httpx`
- `pydantic`
- `python-dotenv`
- YouTube Data API v3 key

---

## Setup Instructions

### 1. Clone the Repository
Clone the repository to your local machine:

```bash
git clone https://github.com/meyyappan055/YT-data-fetcher
cd app
```

### 2. Install Dependencies
Make sure you have Python installed. Then, install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
Create a `.env` file in the project root and add your YouTube Data API v3 key:
```bash
YOUTUBE_API_KEY=your_api_key_here
```
You can get an API key from the [Google Cloud Console](https://console.cloud.google.com/)


### 4. Running the API
To run the FastAPI application locally, use the following command:

```bash
cd scripts
uvicorn main:app --reload
```
This will start the server at http://127.0.0.1:8000. You can access the API documentation at http://127.0.0.1:8000/docs

---

## Usage Instructions

### 1. Endpoint: `/get_videos`
This endpoint allows you to search for YouTube videos and retrieve detailed information.

#### **Request Body:**

```json
{
  "search_query": "your search term",
  "no_of_results": 100
}

```
- `search_query`: The query term to search for on YouTube.  
- `no_of_results`: The number of video results to fetch.

### 2. Saving Data to CSV
Once the video data is fetched, it will be saved to a CSV file named `video_data.csv`. The CSV will include the following columns:

- `Video_url`
- `Title`
- `Description`
- `Channel Title`
- `Tags`
- `Topic`
- `Published at`
- `Views Count`
- `Comment Counts`
- `Duration`
- `Category Name`
- `Transcript`
- `Location`
