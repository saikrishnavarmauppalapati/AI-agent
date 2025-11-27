# youtube_api.py
import re
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from auth import get_credentials  # ensure auth.py exists and returns valid credentials
import socket

# Create YouTube client on demand to avoid import-time credential errors
def _get_youtube_client():
    creds = get_credentials()
    return build("youtube", "v3", credentials=creds)


# ----------------- UTILITIES -----------------
def extract_video_id(url: str) -> Optional[str]:
    """
    Extract 11-char YouTube video id from full URL (supports v= and youtu.be).
    """
    if not isinstance(url, str):
        return None
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:[&\?#]|$)",
        r"youtu\.be\/([0-9A-Za-z_-]{11})(?:[&\?#]|$)"
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def extract_channel_id_from_video(video_id: str) -> Optional[str]:
    try:
        youtube = _get_youtube_client()
        resp = youtube.videos().list(part="snippet", id=video_id).execute()
        items = resp.get("items", [])
        if not items:
            return None
        return items[0]["snippet"].get("channelId")
    except HttpError as e:
        # Return None on API error
        return None
    except Exception:
        return None


# ----------------- SEARCH -----------------
def search_videos(query: str, max_results: int = 5) -> Any:
    """
    Returns list of dicts: {videoId, title, channelTitle} or {"error": "..."}
    """
    try:
        youtube = _get_youtube_client()
        response = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=max_results
        ).execute()

        results = []
        for item in response.get("items", []):
            vid = item["id"].get("videoId")
            snippet = item.get("snippet", {})
            if vid:
                results.append({
                    "videoId": vid,
                    "title": snippet.get("title", ""),
                    "channelTitle": snippet.get("channelTitle", "")
                })
        return results
    except HttpError as e:
        return {"error": f"HttpError: {e}"}
    except socket.error as e:
        return {"error": f"Network error: {e}"}
    except Exception as e:
        return {"error": str(e)}


# ----------------- LIKE VIDEO -----------------
def like_video(video_url: str) -> Dict[str, str]:
    video_id = extract_video_id(video_url)
    if not video_id:
        return {"error": "Invalid video URL"}

    try:
        youtube = _get_youtube_client()
        youtube.videos().rate(id=video_id, rating="like").execute()
        return {"message": "👍 Done! I liked the video for you."}
    except HttpError as e:
        # Provide a friendly error message for common cases
        status = getattr(e, "resp", None)
        if status and getattr(status, "status", None) == "404":
            return {"error": "Video not found or inaccessible (404)."}
        return {"error": f"HttpError: {e}"}
    except Exception as e:
        return {"error": str(e)}


# ----------------- COMMENT VIDEO -----------------
def comment_on_video(video_url: str, text: str) -> Dict[str, str]:
    video_id = extract_video_id(video_url)
    if not video_id:
        return {"error": "Invalid video URL"}
    if not text or not isinstance(text, str):
        return {"error": "Comment text required"}

    try:
        youtube = _get_youtube_client()
        youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {"snippet": {"textOriginal": text}}
                }
            }
        ).execute()
        return {"message": "💬 Done! I commented on the video for you."}
    except HttpError as e:
        # Common API errors: quota, permission, notFound, etc.
        return {"error": f"HttpError: {e}"}
    except Exception as e:
        return {"error": str(e)}


# ----------------- SUBSCRIBE -----------------
def subscribe_channel(video_url: str) -> Dict[str, str]:
    video_id = extract_video_id(video_url)
    if not video_id:
        return {"error": "Invalid video URL"}
    channel_id = extract_channel_id_from_video(video_id)
    if not channel_id:
        return {"error": "Channel not found from video"}

    try:
        youtube = _get_youtube_client()
        youtube.subscriptions().insert(
            part="snippet",
            body={
                "snippet": {
                    "resourceId": {"kind": "youtube#channel", "channelId": channel_id}
                }
            }
        ).execute()
        return {"message": "🔔 Done! Subscribed to the channel for you."}
    except HttpError as e:
        return {"error": f"HttpError: {e}"}
    except Exception as e:
        return {"error": str(e)}


# ----------------- LIKED VIDEOS -----------------
def get_liked_videos(max_results: int = 10) -> Any:
    """
    Returns list of liked videos for the authenticated user,
    each item: {videoId, title, channelTitle}
    """
    try:
        youtube = _get_youtube_client()
        response = youtube.videos().list(
            part="snippet",
            myRating="like",
            maxResults=max_results
        ).execute()

        items = []
        for item in response.get("items", []):
            items.append({
                "videoId": item.get("id"),
                "title": item.get("snippet", {}).get("title", ""),
                "channelTitle": item.get("snippet", {}).get("channelTitle", "")
            })
        return items
    except HttpError as e:
        return {"error": f"HttpError: {e}"}
    except Exception as e:
        return {"error": str(e)}


# ----------------- RECOMMENDED VIDEOS -----------------
def get_recommended_videos(max_results: int = 10) -> Any:
    """
    Recommend videos based on simple keyword extraction from liked videos.
    Returns list of {videoId, title, channelTitle}
    """
    try:
        liked = get_liked_videos(max_results=10)
        if isinstance(liked, dict) and "error" in liked:
            return liked

        recommended = []
        for v in liked:
            title = v.get("title", "")
            # take up to first 4 words as a lightweight keyword query
            keywords = " ".join(title.split()[:4])
            if not keywords:
                continue
            results = search_videos(keywords, max_results=3)
            if isinstance(results, list):
                recommended.extend(results)

        # deduplicate by videoId and limit
        unique = []
        seen = set()
        for r in recommended:
            vid = r.get("videoId")
            if not vid or vid in seen:
                continue
            seen.add(vid)
            unique.append(r)
            if len(unique) >= max_results:
                break

        return unique
    except Exception as e:
        return {"error": str(e)}
