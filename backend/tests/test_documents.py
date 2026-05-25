"""
test_documents.py — QA tests for /api/documents/* endpoints.

Covers:
  TC-DOC-01  Upload valid PDF → 200, correct metadata
  TC-DOC-02  Upload non-PDF file → 400
  TC-DOC-03  Upload empty / corrupt PDF → 422 or 500
  TC-DOC-04  List documents returns uploaded doc
  TC-DOC-05  page_count and chunk_count are non-zero
  TC-DOC-06  Upload same filename twice → two separate doc_ids
  TC-DOC-07  Delete document → removed from list
  TC-DOC-08  Delete non-existent doc_id → still returns deleted=True (idempotent)
  TC-DOC-09  Page URL endpoint returns correct structure
  TC-DOC-10  Tiny 1-page PDF → chunk_count >= 1
"""
import pytest
from conftest import SPEC_PDF, TINY_PDF, FAKE_TXT


class TestDocumentUpload:

    def test_TC_DOC_01_upload_valid_pdf(self, client, uploaded_spec):
        """Valid PDF upload returns 200 with correct metadata structure."""
        doc = uploaded_spec
        assert "doc_id"      in doc,              "Missing doc_id"
        assert "filename"    in doc,              "Missing filename"
        assert "page_count"  in doc,              "Missing page_count"
        assert "chunk_count" in doc,              "Missing chunk_count"
        assert doc["filename"]    == "spec.pdf",  "Filename mismatch"
        assert len(doc["doc_id"]) == 36,          "doc_id should be UUID (36 chars)"

    def test_TC_DOC_02_upload_non_pdf_rejected(self, client):
        """Non-PDF file must return 400."""
        with open(FAKE_TXT, "rb") as f:
            res = client.post("/api/documents/upload",
                              files={"file": ("fake.txt", f, "text/plain")})
        assert res.status_code == 400, f"Expected 400, got {res.status_code}"
        assert "PDF" in res.json()["detail"].upper(), "Error message should mention PDF"

    def test_TC_DOC_03_upload_pdf_disguised_as_txt(self, client):
        """File with .txt extension but sent as PDF should still be rejected."""
        with open(SPEC_PDF, "rb") as f:
            res = client.post("/api/documents/upload",
                              files={"file": ("spec.txt", f, "application/pdf")})
        # Filename extension check should catch this
        assert res.status_code == 400

    def test_TC_DOC_05_page_and_chunk_counts_nonzero(self, client, uploaded_spec):
        """page_count and chunk_count must both be > 0 after upload."""
        doc = uploaded_spec
        assert doc["page_count"]  > 0, f"page_count={doc['page_count']}, expected > 0"
        assert doc["chunk_count"] > 0, f"chunk_count={doc['chunk_count']}, expected > 0"

    def test_TC_DOC_06_same_filename_twice_gets_different_ids(self, client):
        """Uploading same file twice must produce two separate doc_ids."""
        ids = []
        for _ in range(2):
            with open(SPEC_PDF, "rb") as f:
                res = client.post("/api/documents/upload",
                                  files={"file": ("spec.pdf", f, "application/pdf")})
            assert res.status_code == 200
            ids.append(res.json()["doc_id"])
        assert ids[0] != ids[1], "Two uploads of same file must have different doc_ids"

    def test_TC_DOC_10_tiny_pdf_gets_chunks(self, client):
        """Even a 1-page minimal PDF must produce at least 1 chunk."""
        with open(TINY_PDF, "rb") as f:
            res = client.post("/api/documents/upload",
                              files={"file": ("tiny.pdf", f, "application/pdf")})
        assert res.status_code == 200
        assert res.json()["chunk_count"] >= 1


class TestDocumentList:

    def test_TC_DOC_04_list_contains_uploaded_doc(self, client, uploaded_spec):
        """List endpoint must return the uploaded spec document."""
        res = client.get("/api/documents/")
        assert res.status_code == 200
        ids = [d["doc_id"] for d in res.json()]
        assert uploaded_spec["doc_id"] in ids, "Uploaded doc not found in list"

    def test_TC_DOC_04b_list_returns_array(self, client):
        """List endpoint must always return a JSON array."""
        res = client.get("/api/documents/")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_TC_DOC_04c_list_items_have_required_fields(self, client):
        """Every item in list must have doc_id, filename, page_count, chunk_count."""
        res = client.get("/api/documents/")
        for item in res.json():
            assert "doc_id"      in item
            assert "filename"    in item
            assert "page_count"  in item
            assert "chunk_count" in item
            assert item["page_count"]  >= 0
            assert item["chunk_count"] >= 0


class TestDocumentDelete:

    def test_TC_DOC_07_delete_removes_from_list(self, client):
        """Delete a document → it no longer appears in the list."""
        # Upload a fresh doc to delete
        with open(TINY_PDF, "rb") as f:
            up = client.post("/api/documents/upload",
                             files={"file": ("to_delete.pdf", f, "application/pdf")})
        doc_id = up.json()["doc_id"]

        # Delete it
        res = client.delete(f"/api/documents/{doc_id}")
        assert res.status_code == 200
        assert res.json()["deleted"] is True

        # Verify gone from list
        ids = [d["doc_id"] for d in client.get("/api/documents/").json()]
        assert doc_id not in ids, "Deleted doc still appears in list"

    def test_TC_DOC_08_delete_nonexistent_is_idempotent(self, client):
        """Deleting a non-existent doc_id must not crash — return deleted=True."""
        res = client.delete("/api/documents/nonexistent-id-12345")
        assert res.status_code == 200
        assert res.json()["deleted"] is True


class TestPageUrl:

    def test_TC_DOC_09_page_url_returns_structure(self, client, uploaded_spec):
        """Page URL endpoint must return exists and url fields."""
        doc_id = uploaded_spec["doc_id"]
        res = client.get(f"/api/documents/{doc_id}/page-url/1")
        assert res.status_code == 200
        body = res.json()
        assert "exists" in body
        assert "url"    in body
        assert isinstance(body["exists"], bool)
        assert body["url"].startswith("/pages/")

    def test_TC_DOC_09b_page_url_invalid_page_returns_false(self, client, uploaded_spec):
        """Page 9999 should exist=False, not crash."""
        doc_id = uploaded_spec["doc_id"]
        res = client.get(f"/api/documents/{doc_id}/page-url/9999")
        assert res.status_code == 200
        assert res.json()["exists"] is False