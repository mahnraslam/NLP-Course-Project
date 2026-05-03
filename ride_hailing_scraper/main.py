from scrapers.play_store import scrape_play_store
from scrapers.app_store import scrape_app_store
from scrapers.youtube_scraper import scrape_youtube
from scrapers.reddit_scraper import scrape_reddit
from preprocessing.cleaner import preprocess
from db.insert import bulk_insert
import logging

logging.basicConfig(level=logging.INFO)
BRANDS = ["careem", "uber", "indrive", "bykea"]

def run_pipeline(brand: str):
    print(f"\n=== Pipeline for {brand} ===")
    raw = (
        scrape_play_store(brand) +
        scrape_app_store(brand) +
        scrape_youtube(brand) +
        scrape_reddit(brand)
    )
    print(f"Collected {len(raw)} raw reviews")

    for r in raw:
        result = preprocess(r["text"])
        r["cleaned_text"] = result["cleaned_text"]
        r["language"]     = result["language"]

    bulk_insert(raw)
    print(f"=== Done: {brand} ===")

if __name__ == "__main__":
    for brand in BRANDS:
        run_pipeline(brand)
