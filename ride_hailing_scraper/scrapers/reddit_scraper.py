import praw, os, hashlib, logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("reddit")

SEARCH_QUERIES = {
    "careem":  ["Careem Pakistan", "Careem app review"],
    "uber":    ["Uber Pakistan", "Uber Lahore"],
    "indrive": ["inDrive Pakistan", "InDriver review"],
    "bykea":   ["Bykea Pakistan", "Bykea app"],
}

def get_reddit_client():
    return praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT")
    )

def scrape_reddit(brand: str, limit=500) -> list[dict]:
    reddit = get_reddit_client()
    results = []
    for sub in ["pakistan", "karachi", "lahore"]:
        for query in SEARCH_QUERIES[brand]:
            try:
                for post in reddit.subreddit(sub).search(query, limit=20, sort="relevance"):
                    if post.selftext and len(post.selftext) > 10:
                        text = post.selftext.strip()
                        results.append({
                            "brand": brand, "platform": "reddit",
                            "text": text, "rating": None,
                            "date": str(post.created_utc),
                            "hash": hashlib.sha256(text.encode()).hexdigest()
                        })
                    post.comments.replace_more(limit=0)
                    for comment in post.comments.list()[:20]:
                        ctext = comment.body.strip()
                        if len(ctext) > 10:
                            results.append({
                                "brand": brand, "platform": "reddit",
                                "text": ctext, "rating": None,
                                "date": str(comment.created_utc),
                                "hash": hashlib.sha256(ctext.encode()).hexdigest()
                            })
            except Exception as e:
                logger.warning(f"Reddit error: {e}")
    logger.info(f"Reddit: {len(results)} posts for {brand}")
    return results
