from services.gemini import embed_batch, embed_text
from services import vector_store


def embed_and_store(chunks: list[dict], doc_id: str, filename: str):
    """Embed all chunks and store in ChromaDB."""
    texts = [c["text"] for c in chunks]
    print(f"[embedder] Embedding {len(texts)} chunks for {filename}…")
    embeddings = embed_batch(texts)
    vector_store.add(chunks, embeddings, doc_id, filename)
    print(f"[embedder] Stored {len(texts)} chunks for doc_id={doc_id}")


def embed_query(text: str) -> list[float]:
    """Embed a single query string."""
    return embed_text(text)
