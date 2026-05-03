import psycopg2, os, logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("db")

def get_conn():
    return psycopg2.connect(os.getenv("DB_URL"))

def bulk_insert(reviews: list[dict]) -> int:
    conn = get_conn()
    inserted = 0
    with conn.cursor() as cur:
        for r in reviews:
            try:
                cur.execute("""
                    INSERT INTO reviews
                        (brand, platform, text, cleaned_text, language, rating, date, hash)
                    VALUES
                        (%(brand)s, %(platform)s, %(text)s,
                         %(cleaned_text)s, %(language)s,
                         %(rating)s, %(date)s, %(hash)s)
                    ON CONFLICT (hash) DO NOTHING
                """, r)
                inserted += 1
            except Exception as e:
                logger.warning(f"Skip row: {e}")
    conn.commit()
    conn.close()
    logger.info(f"Inserted {inserted}/{len(reviews)}")
    return inserted
