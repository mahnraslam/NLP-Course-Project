import re
from langdetect import detect, LangDetectException

ROMAN_URDU_MAP = {
    "accha": "acha", "kharab": "kharab", "khrab": "kharab",
    "drvr": "driver", "thek": "theek", "theak": "theek",
    "bekar": "bekaar", "bakar": "bekaar", "zbrdst": "zabardast",
    "mushkel": "mushkil", "gandha": "ganda", "mhangi": "mehangi",
    "nhi": "nahi", "blkl": "bilkul",
}

ROMAN_URDU_MARKERS = [
    "acha", "theek", "nahi", "bahut", "karo", "bhai", "yar",
    "kya", "hai", "hain", "tha", "mera", "meri"
]

def clean_text(text: str) -> str:
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[^\u0000-\uD7FF\uE000-\uFFFF]', '', text, flags=re.UNICODE)
    text = re.sub(r'[^\w\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def detect_language(text: str) -> str:
    try:
        if any(w in text.lower() for w in ROMAN_URDU_MARKERS):
            return "roman_urdu"
        return detect(text)
    except LangDetectException:
        return "unknown"

def normalize_roman_urdu(text: str) -> str:
    return " ".join(ROMAN_URDU_MAP.get(w, w) for w in text.split())

def preprocess(raw_text: str) -> dict:
    cleaned = clean_text(raw_text)
    return {
        "cleaned_text": normalize_roman_urdu(cleaned),
        "language":     detect_language(cleaned)
    }
