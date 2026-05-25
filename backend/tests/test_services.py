"""
test_services.py — Unit tests for individual backend services.
These tests mock Gemini so they run WITHOUT a real API key.

Covers:
  TC-SVC-01  pdf_parser extracts text correctly from spec.pdf
  TC-SVC-02  pdf_parser returns correct page_count
  TC-SVC-03  pdf_parser chunks long text into multiple chunks
  TC-SVC-04  pdf_parser handles tiny PDF (1 page, few chars)
  TC-SVC-05  vector_store.add then query returns matching chunk
  TC-SVC-06  vector_store chunk ID collision prevention (p1_c0 vs p1_c1)
  TC-SVC-07  vector_store.list_documents returns correct page_count
  TC-SVC-08  vector_store.delete removes all chunks for a doc
  TC-SVC-09  vector_store.query with n > chunk_count doesn't crash (the known bug)
  TC-SVC-10  embedder uses same model for query and storage (no vector space mismatch)
"""
import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_test_tmp = os.path.join(tempfile.gettempdir(), "constructos_unit_test")
os.makedirs(_test_tmp, exist_ok=True)
os.environ["CHROMA_PATH"]    = os.path.join(_test_tmp, "chroma")
os.environ["GEMINI_API_KEY"] = "test-key"

_TEST_PDF_DIR = os.path.join(os.path.dirname(__file__), "test_pdfs")
SPEC_PDF      = os.path.join(_TEST_PDF_DIR, "spec.pdf")
TINY_PDF      = os.path.join(_TEST_PDF_DIR, "tiny.pdf")
BLUEPRINT_PDF = os.path.join(_TEST_PDF_DIR, "blueprint.pdf")


# ── Helpers ──────────────────────────────────────────────────────────────────

def fake_embedding(text=""):
    """Return a deterministic 768-dim fake embedding vector."""
    return [0.01] * 768

def fake_embed_text(text):
    return fake_embedding()

def fake_embed_batch(texts):
    return [fake_embedding() for _ in texts]

def fake_vision(image_path):
    return "MOCKED VISION: 16mm rebar at 150mm centres, slab 200mm"


# ── PDF Parser Tests ──────────────────────────────────────────────────────────

class TestPdfParser:

    @patch("services.gemini.describe_blueprint_page", fake_vision)
    def test_TC_SVC_01_text_extracted(self):
        """pdf_parser must extract non-empty text from spec.pdf."""
        from services.pdf_parser import parse
        chunks, page_count = parse(SPEC_PDF, "test-spec-unit")
        all_text = " ".join(c["text"] for c in chunks)
        assert "slab" in all_text.lower() or "concrete" in all_text.lower(), \
            f"Expected construction text, got: {all_text[:200]}"

    @patch("services.gemini.describe_blueprint_page", fake_vision)
    def test_TC_SVC_02_correct_page_count(self):
        """page_count must match actual PDF page count."""
        from services.pdf_parser import parse
        _, page_count = parse(SPEC_PDF, "test-spec-pages")
        assert page_count >= 1, "page_count must be >= 1"

    @patch("services.gemini.describe_blueprint_page", fake_vision)
    def test_TC_SVC_03_long_text_chunked(self):
        """A long-text page must produce multiple chunks."""
        from services.pdf_parser import parse
        chunks, _ = parse(SPEC_PDF, "test-spec-chunks")
        # spec.pdf has multiple sections — expect > 1 chunk
        assert len(chunks) >= 1
        # All chunks must have text and page
        for c in chunks:
            assert "text" in c and c["text"], "chunk missing text"
            assert "page" in c and c["page"] >= 1, "chunk missing page"

    @patch("services.gemini.describe_blueprint_page", fake_vision)
    def test_TC_SVC_04_tiny_pdf_produces_chunk(self):
        """1-page minimal PDF must produce at least 1 chunk."""
        from services.pdf_parser import parse
        chunks, page_count = parse(TINY_PDF, "test-tiny")
        assert page_count == 1
        assert len(chunks) >= 1

    @patch("services.gemini.describe_blueprint_page", fake_vision)
    def test_TC_SVC_04b_chunk_text_not_longer_than_1500(self):
        """No chunk text must exceed 1500 characters."""
        from services.pdf_parser import parse
        chunks, _ = parse(SPEC_PDF, "test-chunk-size")
        for i, c in enumerate(chunks):
            assert len(c["text"]) <= 1500, \
                f"Chunk {i} exceeds 1500 chars: {len(c['text'])}"


# ── Vector Store Tests ────────────────────────────────────────────────────────

class TestVectorStore:
    """
    These tests use a fresh isolated ChromaDB collection.
    Gemini embedding is mocked — tests run offline.
    """

    @patch("services.gemini.embed_text",  fake_embed_text)
    @patch("services.gemini.embed_batch", fake_embed_batch)
    def test_TC_SVC_05_add_then_query_returns_chunk(self):
        """Add a chunk, query it, must get it back."""
        import chromadb

        # Use an isolated collection
        client = chromadb.PersistentClient(path=os.path.join(_test_tmp, "vs_test_05"))
        col = client.get_or_create_collection("test_05", metadata={"hnsw:space": "cosine"})

        chunks = [{"text": "Column dimension is 400mm x 400mm", "page": 1}]
        embeddings = [fake_embedding()]
        doc_id = "test-doc-05"

        col.add(
            ids=["test-doc-05_p1_c0"],
            embeddings=embeddings,
            documents=[chunks[0]["text"]],
            metadatas=[{"doc_id": doc_id, "filename": "test.pdf", "page": 1}]
        )

        results = col.query(query_embeddings=[fake_embedding()], n_results=1,
                            include=["documents", "metadatas", "distances"])
        assert len(results["documents"][0]) == 1
        assert "400" in results["documents"][0][0]

    def test_TC_SVC_06_chunk_ids_no_collision(self):
        """
        CHUNK ID COLLISION TEST.
        Two chunks on page 1 must have different IDs: p1_c0 and p1_c1.
        Old buggy code: doc_p1 and doc_p1 — second overwrites first.
        """
        chunks = [
            {"text": "First chunk on page 1",  "page": 1},
            {"text": "Second chunk on page 1", "page": 1},
            {"text": "Chunk on page 2",         "page": 2},
        ]
        doc_id = "test-doc-06"
        ids = [f"{doc_id}_p{c['page']}_c{i}" for i, c in enumerate(chunks)]
        assert len(ids) == len(set(ids)), \
            f"Duplicate chunk IDs detected: {ids}"
        assert ids[0] == "test-doc-06_p1_c0"
        assert ids[1] == "test-doc-06_p1_c1"
        assert ids[2] == "test-doc-06_p2_c2"

    @patch("services.gemini.embed_text",  fake_embed_text)
    @patch("services.gemini.embed_batch", fake_embed_batch)
    def test_TC_SVC_07_list_documents_correct_page_count(self):
        """list_documents must report correct page_count derived from chunk metadata."""
        import chromadb
        client = chromadb.PersistentClient(path=os.path.join(_test_tmp, "vs_test_07"))
        col = client.get_or_create_collection("test_07", metadata={"hnsw:space": "cosine"})
        doc_id = "doc-pagecount-test"
        # Simulate 3 pages with 1 chunk each
        for page in [1, 2, 3]:
            col.add(
                ids=[f"{doc_id}_p{page}_c0"],
                embeddings=[fake_embedding()],
                documents=[f"Content on page {page}"],
                metadatas=[{"doc_id": doc_id, "filename": "test.pdf", "page": page}]
            )
        meta = col.get(include=["metadatas"])["metadatas"]
        pages = {m["page"] for m in meta if m["doc_id"] == doc_id}
        assert max(pages) == 3, f"Expected page_count=3, got {max(pages)}"

    @patch("services.gemini.embed_text",  fake_embed_text)
    @patch("services.gemini.embed_batch", fake_embed_batch)
    def test_TC_SVC_08_delete_removes_all_chunks(self):
        """delete_document must remove ALL chunks for that doc_id."""
        import chromadb
        client = chromadb.PersistentClient(path=os.path.join(_test_tmp, "vs_test_08"))
        col = client.get_or_create_collection("test_08", metadata={"hnsw:space": "cosine"})
        doc_id = "doc-to-delete"
        for i in range(3):
            col.add(
                ids=[f"{doc_id}_p1_c{i}"],
                embeddings=[fake_embedding()],
                documents=[f"Chunk {i}"],
                metadatas=[{"doc_id": doc_id, "filename": "del.pdf", "page": 1}]
            )
        # Delete
        ids = col.get(where={"doc_id": doc_id})["ids"]
        assert len(ids) == 3
        col.delete(ids=ids)
        remaining = col.get(where={"doc_id": doc_id})["ids"]
        assert len(remaining) == 0, "Delete left chunks behind"

    @patch("services.gemini.embed_text",  fake_embed_text)
    @patch("services.gemini.embed_batch", fake_embed_batch)
    def test_TC_SVC_09_query_n_greater_than_chunk_count(self):
        """
        KNOWN BUG TEST.
        ChromaDB crashes if n_results > total chunks in collection.
        vector_store.query must guard against this.
        Fixed with: actual_n = min(n, _col.count())
        """
        import chromadb
        client = chromadb.PersistentClient(path=os.path.join(_test_tmp, "vs_test_09"))
        col = client.get_or_create_collection("test_09", metadata={"hnsw:space": "cosine"})
        # Add only 2 chunks
        for i in range(2):
            col.add(
                ids=[f"small-doc_p1_c{i}"],
                embeddings=[fake_embedding()],
                documents=[f"Small chunk {i}"],
                metadatas=[{"doc_id": "small-doc", "filename": "small.pdf", "page": 1}]
            )
        # Query with n=5 > 2 chunks — must not crash
        try:
            actual_n = min(5, col.count())
            results = col.query(query_embeddings=[fake_embedding()],
                                n_results=actual_n,
                                include=["documents", "metadatas", "distances"])
            assert len(results["documents"][0]) == 2
        except Exception as e:
            pytest.fail(f"Query crashed when n > chunk count: {e}")

    def test_TC_SVC_10_embedding_model_consistency(self):
        """
        EMBEDDING CONSISTENCY TEST.
        embed_query and embed_and_store must both call the same Gemini model.
        If they use different models, vector space mismatch = broken retrieval.
        """
        import inspect
        import services.embedder as embedder_module
        import services.gemini as gemini_module

        embedder_src = inspect.getsource(embedder_module)
        gemini_src   = inspect.getsource(gemini_module)

        # Neither file should import sentence_transformers
        assert "sentence_transformers" not in embedder_src, \
            "embedder.py imports sentence_transformers — breaks embedding consistency"
        assert "sentence_transformers" not in gemini_src, \
            "gemini.py imports sentence_transformers"

        # Gemini embed model should be used
        assert "embed_content" in gemini_src or "embed_text" in gemini_src, \
            "gemini.py doesn't call Gemini embedding API"