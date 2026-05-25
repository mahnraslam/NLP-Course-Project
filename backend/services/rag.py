import os
import logging
from services import embedder, vector_store
from services.gemini import generate, generate_with_images
from models.schemas import QueryResponse, Citation

logger = logging.getLogger(__name__)

PAGES_DIR = os.getenv("PAGES_PATH", "storage/pages")

# Maximum blueprint page images to attach per query.
# Gemini Flash handles up to ~16 images per request, but we keep it low
# to control latency and token cost. The top-3 pages by relevance are enough
# to give the model a strong visual signal.
MAX_VISUAL_PAGES = 3

_SYSTEM = """You are ConstructOS — an expert construction document intelligence assistant.
You specialise in engineering drawings, structural specifications, RFIs, and site reports.
Your answers are used by engineers and site managers to make technical decisions.

STRICT RULES:
1. Answer ONLY from the provided document context. Never use general knowledge.
2. If the answer is not in the context, respond exactly: "NOT FOUND IN DOCUMENTS"
3. Always cite your source as: (Source N — filename, Page X)
4. For technical values (dimensions, grades, rebar, loads), quote the exact number from the document.
5. Be precise and concise. Engineers need facts, not padding."""

_VISUAL_SYSTEM = """You are ConstructOS — an expert construction document intelligence assistant.
You specialise in engineering drawings, structural specifications, RFIs, and site reports.
Your answers are used by engineers and site managers to make technical decisions.

You are being provided with BOTH:
  • Extracted text context from the relevant pages
  • The actual page images so you can directly observe the drawings

STRICT RULES:
1. Use BOTH the text context AND what you can visually see in the images to form your answer.
2. When the text is incomplete or absent, extract information directly from the drawing.
3. If the answer is not in the context or visible in the images, respond: "NOT FOUND IN DOCUMENTS"
4. Always cite your source as: (Source N — filename, Page X)
5. For technical values (dimensions, grades, rebar), quote the exact number you see.
6. Be precise and concise. Engineers need facts, not padding.
7. If you can see something in the drawing that the text missed, explicitly note it as
   "(visually observed in drawing)" so the engineer knows the source."""

_ANSWER_FORMAT = """
Structure your answer as:
**Answer:** [1-2 sentence direct answer]
**Technical Detail:** [exact values, materials, codes — if available]
**Source:** [filename, Page N — verbatim quote from the document, max 100 chars]
"""

_VISUAL_ANSWER_FORMAT = """
Structure your answer as:
**Answer:** [1-2 sentence direct answer]
**Technical Detail:** [exact values, materials, codes — include whether from text or drawing]
**Visual Observations:** [anything significant you can see in the drawing images that supplements the text]
**Source:** [filename, Page N]
"""


def _build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks as a numbered source block."""
    lines = []
    for i, c in enumerate(chunks, 1):
        lines.append(f"[Source {i}: {c['filename']}, Page {c['page']}]\n{c['text']}")
    return "\n\n---\n\n".join(lines)


def _image_paths_for_chunks(chunks: list[dict], max_images: int = MAX_VISUAL_PAGES) -> list[str]:
    """
    Return filesystem paths for the page PNGs corresponding to the top chunks.
    De-duplicates by (doc_id, page) and caps at max_images to keep requests lean.
    Only paths that actually exist on disk are returned.
    """
    seen: set[tuple] = set()
    paths: list[str] = []
    for c in chunks:
        key = (c["doc_id"], c["page"])
        if key in seen:
            continue
        seen.add(key)
        path = os.path.join(PAGES_DIR, f"{c['doc_id']}_page_{c['page']}.png")
        if os.path.exists(path):
            paths.append(path)
        else:
            logger.debug(f"[rag] Page image not on disk: {path}")
        if len(paths) >= max_images:
            break
    return paths


def _citation_image_url(c: dict) -> str | None:
    """
    Return the static URL for a chunk's page image if it exists on disk.
    The FastAPI app mounts storage/pages at /pages, so the URL is stable.
    """
    path = os.path.join(PAGES_DIR, f"{c['doc_id']}_page_{c['page']}.png")
    if os.path.exists(path):
        return f"/pages/{c['doc_id']}_page_{c['page']}.png"
    return None


def answer(
    question: str,
    doc_ids: list[str] | None,
    top_k: int = 5,
    visual: bool = False,
) -> QueryResponse:
    """
    Answer a construction document question.

    visual=False (default): text-only RAG — identical to previous behaviour.
    visual=True:            multimodal RAG — top page images are sent to
                            Gemini Vision alongside the extracted text so the
                            model can *see* the drawings when answering.

    Either way, every Citation now carries an image_url pointing to the
    pre-rendered PNG for that page, so the frontend can show inline previews.
    """
    # 1. Embed question and retrieve relevant chunks
    q_emb  = embedder.embed_query(question)
    chunks = vector_store.query(q_emb, doc_ids, n=top_k)

    if not chunks:
        return QueryResponse(
            question  = question,
            answer    = "NOT FOUND IN DOCUMENTS — no documents have been uploaded yet.",
            citations = [],
        )

    # 2. Build text context
    context = _build_context(chunks)

    if visual:
        # 3a. Visual path: load page images for top chunks
        image_paths = _image_paths_for_chunks(chunks)
        n_images = len(image_paths)
        logger.info(f"[rag] Visual mode: attaching {n_images} page image(s) for query")

        prompt = f"""{_VISUAL_SYSTEM}

EXTRACTED TEXT CONTEXT:
{context}

QUESTION: {question}

{_VISUAL_ANSWER_FORMAT}

Note: {n_images} blueprint page image(s) are also attached — use them to supplement
the text context above. If you can read dimensions, annotations, or details directly
from the drawing that are not in the text, include them in your answer.
"""
        answer_text = generate_with_images(prompt, image_paths)

    else:
        # 3b. Text-only path (original behaviour)
        prompt = f"""{_SYSTEM}

DOCUMENT CONTEXT:
{context}

QUESTION: {question}

{_ANSWER_FORMAT}
"""
        answer_text = generate(prompt)

    # 4. Build citations — always include image_url now so the UI can render previews
    citations = [
        Citation(
            doc_id          = c["doc_id"],
            filename        = c["filename"],
            page_num        = c["page"],
            chunk_text      = c["text"][:300],
            relevance_score = c["relevance_score"],
            image_url       = _citation_image_url(c),
        )
        for c in chunks
    ]

    return QueryResponse(question=question, answer=answer_text, citations=citations)
 