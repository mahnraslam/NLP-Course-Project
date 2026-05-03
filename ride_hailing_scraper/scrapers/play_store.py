import time, hashlib, logging
from google_play_scraper import reviews, Sort

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("play_store")

APP_IDS = {
    "careem":  "com.careem.acma",
    "uber":    "com.ubercab",
    "indrive": "sinet.startup.inDriver",
    "bykea":   "com.bykea.pk",
}

def scrape_play_store(brand: str, count: int = 5000) -> list[dict]:
    app_id = APP_IDS[brand]
    all_reviews = []
    continuation_token = None

    while len(all_reviews) < count:
        try:
            result, continuation_token = reviews(
                app_id,
                lang="en",
                country="pk",
                sort=Sort.NEWEST,
                count=200,
                continuation_token=continuation_token
            )
            if not result:
                break
            for r in result:
                text = r["content"].strip()
                if len(text) < 5:
                    continue
                all_reviews.append({
                    "brand":    brand,
                    "platform": "play_store",
                    "text":     text,
                    "rating":   r["score"],
                    "date":     r["at"].isoformat(),
                    "hash":     hashlib.sha256(text.encode()).hexdigest()
                })
            logger.info(f"Fetched {len(all_reviews)} reviews for {brand}")
            time.sleep(2.5)  # prevents IP ban
            if not continuation_token:
                break
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(10)

    return all_reviews
