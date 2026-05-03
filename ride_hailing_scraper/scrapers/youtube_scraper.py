from googleapiclient.discovery import build
import os, hashlib, logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("youtube")

def get_youtube_client():
    return build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))

def search_brand_videos(youtube, brand: str, max_results=10) -> list[str]:
    response = youtube.search().list(
        q=f"{brand} Pakistan review 2024", part="id", type="video",
        maxResults=max_results, relevanceLanguage="en"
    ).execute()
    return [item["id"]["videoId"] for item in response.get("items", [])]

def fetch_comments(youtube, video_id: str, brand: str) -> list[dict]:
    comments = []
    page_token = None
    while True:
        try:
            resp = youtube.commentThreads().list(
                part="snippet", videoId=video_id,
                maxResults=100, pageToken=page_token
            ).execute()
            for item in resp.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                text = snippet["textDisplay"].strip()
                comments.append({
                    "brand":    brand,
                    "platform": "youtube",
                    "text":     text,
                    "rating":   None,
                    "date":     snippet["publishedAt"],
                    "hash":     hashlib.sha256(text.encode()).hexdigest()
                })
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        except Exception as e:
            logger.warning(f"Comment error: {e}")
            break
    return comments

def scrape_youtube(brand: str) -> list[dict]:
    yt = get_youtube_client()
    video_ids = search_brand_videos(yt, brand)
    all_comments = []
    for vid in video_ids:
        all_comments.extend(fetch_comments(yt, vid, brand))
    logger.info(f"YouTube: {len(all_comments)} for {brand}")
    return all_comments
