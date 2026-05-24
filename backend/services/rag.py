from services import embedder, vector_store
from services.gemini import generate
from models.schemas import QueryResponse, Citation

_SYSTEM = """You are ConstructOS — an expert construction document intelligence assistant.
You specialise in engineering drawings, structural specifications, RFIs, and site reports.
Your answers are used by engineers and site managers to make technical decisions.

STRICT RULES:
1. Answer ONLY from the provided document context. Never use general knowledge.
2. If the answer is not in the context, respond exactly: "NOT FOUND IN DOCUMENTS"
3. Always cite your source as: (Source N — filename, Page X)
4. For technical values (dimensions, grades, rebar, loads), quote the exact number from the document.
5. Be precise and concise. Engineers need facts, not padding."""

_ANSWER_FORMAT = """
Structure your answer as:
**Answer:** [1-2 sentence direct answer]
**Technical Detail:** [exact values, materials, codes — if available]
**Source:** [filename, Page N — verbatim quote from the document, max 100 chars]
"""


def answer(question: str, doc_ids: list[str] | None, top_k: int = 5) -> QueryResponse:
    # 1. Embed question and retrieve relevant chunks
    q_emb  = embedder.embed_query(question)
    chunks = vector_store.query(q_emb, doc_ids, n=top_k)

    if not chunks:
        return QueryResponse(
            question  = question,
            answer    = "NOT FOUND IN DOCUMENTS — no documents have been uploaded yet.",
            citations = [],
        )

    # 2. Build context block with numbered sources
    context_lines = []
    for i, c in enumerate(chunks, 1):
        context_lines.append(
            f"[Source {i}: {c['filename']}, Page {c['page']}]\n{c['text']}"
        )
    context = "\n\n---\n\n".join(context_lines)

    # 3. Construction-domain prompt
    prompt = f"""{_SYSTEM}

DOCUMENT CONTEXT:
{context}

QUESTION: {question}

{_ANSWER_FORMAT}
"""

    answer_text = generate(prompt)

    # 4. Build citation objects
    citations = [
        Citation(
            doc_id          = c["doc_id"],
            filename        = c["filename"],
            page_num        = c["page"],
            chunk_text      = c["text"][:300],
            relevance_score = c["relevance_score"],
        )
        for c in chunks
    ]

    return QueryResponse(question=question, answer=answer_text, citations=citations)
