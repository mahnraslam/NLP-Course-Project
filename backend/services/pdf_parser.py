import os
import pdfplumber
from pdf2image import convert_from_path
from services.gemini import describe_blueprint_page
from dotenv import load_dotenv

load_dotenv()

PAGES_PATH  = os.getenv("PAGES_PATH",  "storage/pages")
UPLOAD_PATH = os.getenv("UPLOAD_PATH", "storage/uploads")

# Pages with fewer characters than this are treated as drawing-heavy
# and get vision enrichment via Gemini
_VISION_THRESHOLD = 200


def parse_pdf(file_path: str, doc_id: str) -> tuple[list[dict], int]:
    """
    Parse a PDF into chunks suitable for embedding.

    Returns:
        chunks  — list of {text, page} dicts
        page_count — total pages in the PDF

    Each chunk is a page-level text block (≤ 1500 chars).
    Drawing-heavy pages (text < _VISION_THRESHOLD chars) get Gemini vision
    description appended so blueprint content is searchable.
    """
    doc_pages_dir = os.path.join(PAGES_PATH, doc_id)
    os.makedirs(doc_pages_dir, exist_ok=True)

    pages_text = []

    # ── 1. Extract text per page ──────────────────────────────────────────
    with pdfplumber.open(file_path) as pdf:
        page_count = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            text = (page.extract_text() or "").strip()
            pages_text.append({"page_num": i + 1, "text": text, "image_path": None})

    # ── 2. Render pages as PNG (for blueprint viewer + vision) ────────────
    try:
        images = convert_from_path(file_path, dpi=150)
        for i, img in enumerate(images):
            img_path = os.path.join(doc_pages_dir, f"page_{i + 1}.png")
            img.save(img_path, "PNG")
            if i < len(pages_text):
                pages_text[i]["image_path"] = img_path
    except Exception as e:
        print(f"[pdf_parser] Image render failed (poppler missing?): {e}")

    # ── 3. Vision enrichment for drawing-heavy pages ──────────────────────
    for page in pages_text:
        if len(page["text"]) < _VISION_THRESHOLD and page["image_path"]:
            print(f"[pdf_parser] Vision enriching page {page['page_num']}…")
            vision_text = describe_blueprint_page(page["image_path"])
            if vision_text:
                page["text"] += f"\n[VISUAL CONTENT — ENGINEERING DRAWING]:\n{vision_text}"

    # ── 4. Chunk each page (split long pages into ≤ 1500-char chunks) ─────
    chunks = []
    for page in pages_text:
        text = page["text"].strip()
        if not text:
            continue
        # Split into ~1500-char chunks with 100-char overlap
        step = 1400
        if len(text) <= 1500:
            chunks.append({"text": text, "page": page["page_num"]})
        else:
            start = 0
            while start < len(text):
                chunk_text = text[start: start + 1500]
                chunks.append({"text": chunk_text, "page": page["page_num"]})
                start += step

    return chunks, page_count
