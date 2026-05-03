from app_store_scraper import AppStore
import hashlib, logging

logger = logging.getLogger("app_store")

APP_STORE_IDS = {
    "careem":  592323604,
    "uber":    368677368,
    "indrive": 1087435196,
    "bykea":   1227745762,
}

def scrape_app_store(brand: str, count: int = 2000) -> list[dict]:
    app = AppStore(country="pk", app_name=brand, app_id=APP_STORE_IDS[brand])
    app.review(how_many=count)

    results = []
    for r in app.reviews:
        text = r.get("review", "").strip()
        if len(text) < 5:
            continue
        results.append({
            "brand":    brand,
            "platform": "app_store",
            "text":     text,
            "rating":   r.get("rating"),
            "date":     str(r.get("date", "")),
            "hash":     hashlib.sha256(text.encode()).hexdigest()
        })
    logger.info(f"App Store: {len(results)} reviews for {brand}")
    return results
