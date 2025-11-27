from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

from youtube_api import (
    search_videos,
    get_liked_videos,
    get_recommended_videos,
    like_video,
    comment_on_video,
    subscribe_channel
)

app = FastAPI()

# CORS for public access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/search")
def search(query: str):
    return search_videos(query)

@app.get("/liked")
def liked():
    return get_liked_videos()

@app.get("/recommend")
def recommend():
    return get_recommended_videos()

@app.get("/like")
def like(videoUrl: str):
    return like_video(videoUrl)

@app.get("/comment")
def comment(videoUrl: str, text: str):
    return comment_on_video(videoUrl, text)

@app.get("/subscribe")
def subscribe(videoUrl: str):
    return subscribe_channel(videoUrl)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
