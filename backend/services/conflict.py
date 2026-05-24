import json
from services import embedder, vector_store
from services.gemini import generate_json
from models.schemas import ConflictItem, ConflictResponse

# Construction conflict topics to check between two documents.
# Each topic is embedded and used to retrieve relevant chunks from both docs.
# Maximum 10 LLM calls total — one per topic (not O(n²) brute force).
_TOPICS = [
    "slab thickness concrete grade strength",
    "rebar size diameter spacing reinforcement",
    "column beam dimensions cross section",
    "wall thickness partition structural",
    "floor level elevation datum height",
    "door window opening size dimension",
    "waterproofing membrane specification material",
    "fire rating insulation protection",
    "structural load capacity bearing",
    "foundation footing depth dimension",
]


def detect(doc_id_a: str, doc_id_b: str, filename_a: str, filename_b: str) -> ConflictResponse:
    """
    Smart conflict detection: 10 topic-targeted retrievals, 10 LLM calls max.
    Returns ConflictResponse with all found conflicts.
    """
    conflicts: list[ConflictItem] = []

    for topic in _TOPICS:
        topic_emb = embedder.embed_query(topic)

        chunks_a = vector_store.query(topic_emb, [doc_id_a], n=2)
        chunks_b = vector_store.query(topic_emb, [doc_id_b], n=2)

        if not chunks_a or not chunks_b:
            continue

        # Take the top chunk from each doc for this topic
        ca = chunks_a[0]
        cb = chunks_b[0]

        # Skip if relevance is too low (likely unrelated)
        if ca["relevance_score"] < 0.3 or cb["relevance_score"] < 0.3:
            continue

        prompt = f"""You are a construction document conflict checker.
Compare these two excerpts from different construction documents and identify contradictions.

DOC A — {filename_a}, Page {ca['page']}:
\"\"\"{ca['text'][:400]}\"\"\"

DOC B — {filename_b}, Page {cb['page']}:
\"\"\"{cb['text'][:400]}\"\"\"

Topic being checked: {topic}

If there is a technical contradiction (e.g. different dimensions, grades, specs for the same element):
Respond with ONLY valid JSON:
{{"conflict": true, "severity": "high|medium|low", "description": "one sentence explaining the contradiction", "quote_a": "exact phrase from doc A (max 80 chars)", "quote_b": "exact phrase from doc B (max 80 chars)"}}

If there is NO contradiction or both excerpts are about different things:
Respond with ONLY: {{"conflict": false}}

Do not add any text outside the JSON."""

        raw = generate_json(prompt).strip()

        # Strip markdown code fences if Gemini wraps it
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            print(f"[conflict] JSON parse failed for topic '{topic}': {raw[:100]}")
            continue

        if result.get("conflict"):
            conflicts.append(ConflictItem(
                severity    = result.get("severity", "medium"),
                topic       = topic,
                description = result.get("description", ""),
                quote_a     = result.get("quote_a", ca["text"][:80]),
                quote_b     = result.get("quote_b", cb["text"][:80]),
                page_a      = ca["page"],
                page_b      = cb["page"],
                filename_a  = filename_a,
                filename_b  = filename_b,
            ))

    return ConflictResponse(
        doc_id_a  = doc_id_a,
        doc_id_b  = doc_id_b,
        conflicts = conflicts,
        total     = len(conflicts),
    )
