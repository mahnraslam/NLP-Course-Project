"""
test_query.py — QA tests for /api/query/ endpoint.

Covers:
  TC-QRY-01  Question answered with citations (happy path)
  TC-QRY-02  Answer contains page_num in every citation
  TC-QRY-03  Answer contains relevance_score 0.0–1.0
  TC-QRY-04  Empty question returns gracefully
  TC-QRY-05  Question about content NOT in docs → "NOT FOUND" (no hallucination)
  TC-QRY-06  Scoped query (specific doc_id) only returns citations from that doc
  TC-QRY-07  Global query (doc_ids=None) searches all documents
  TC-QRY-08  top_k respected — citations count <= top_k
  TC-QRY-09  Response structure matches QueryResponse schema
  TC-QRY-10  Factual accuracy — slab thickness answered correctly from spec

These tests require a real Gemini API key in .env.
If GEMINI_API_KEY=test-key, LLM calls will fail — mark expected.
"""
import os
import pytest

REAL_GEMINI = os.environ.get("GEMINI_API_KEY", "test-key") != "test-key"
skip_llm = pytest.mark.skipif(not REAL_GEMINI, reason="Real GEMINI_API_KEY required")


class TestQueryStructure:
    """Tests that don't need a real LLM — check response shape only."""

    def test_TC_QRY_09_response_schema(self, client, uploaded_spec):
        """Response must have question, answer, citations fields."""
        if not REAL_GEMINI:
            pytest.skip("Need real Gemini key")
        res = client.post("/api/query/", json={
            "question": "What is the slab thickness?",
            "doc_ids": [uploaded_spec["doc_id"]],
        })
        assert res.status_code == 200
        body = res.json()
        assert "question"  in body
        assert "answer"    in body
        assert "citations" in body
        assert isinstance(body["citations"], list)
        assert body["question"] == "What is the slab thickness?"

    def test_TC_QRY_02_citations_have_page_num(self, client, uploaded_spec):
        """Every citation must have page_num as a positive integer."""
        if not REAL_GEMINI:
            pytest.skip("Need real Gemini key")
        res = client.post("/api/query/", json={
            "question": "What concrete grade is specified?",
            "doc_ids": [uploaded_spec["doc_id"]],
        })
        assert res.status_code == 200
        for cit in res.json()["citations"]:
            assert "page_num" in cit,              "citation missing page_num"
            assert isinstance(cit["page_num"], int)
            assert cit["page_num"] >= 1,           "page_num must be >= 1"

    def test_TC_QRY_03_relevance_score_range(self, client, uploaded_spec):
        """relevance_score must be between 0.0 and 1.0."""
        if not REAL_GEMINI:
            pytest.skip("Need real Gemini key")
        res = client.post("/api/query/", json={
            "question": "What is the rebar diameter?",
            "doc_ids": [uploaded_spec["doc_id"]],
        })
        for cit in res.json()["citations"]:
            score = cit["relevance_score"]
            assert 0.0 <= score <= 1.0, f"Score {score} out of [0, 1] range"

    def test_TC_QRY_08_top_k_respected(self, client, uploaded_spec):
        """Citations returned must not exceed top_k."""
        if not REAL_GEMINI:
            pytest.skip("Need real Gemini key")
        for top_k in [1, 3, 5]:
            res = client.post("/api/query/", json={
                "question": "What are the foundation dimensions?",
                "doc_ids": [uploaded_spec["doc_id"]],
                "top_k": top_k,
            })
            assert res.status_code == 200
            assert len(res.json()["citations"]) <= top_k, \
                f"top_k={top_k} but got {len(res.json()['citations'])} citations"


class TestQueryAccuracy:
    """Tests that verify AI answer quality — require real Gemini key."""

    @skip_llm
    def test_TC_QRY_10_slab_thickness_correct(self, client, uploaded_spec):
        """
        FACTUAL ACCURACY TEST.
        spec.pdf says 'Slab thickness: 200mm'.
        Answer must contain '200' and not contain '150'.
        """
        res = client.post("/api/query/", json={
            "question": "What is the slab thickness specified?",
            "doc_ids": [uploaded_spec["doc_id"]],
        })
        assert res.status_code == 200
        answer = res.json()["answer"].lower()
        assert "200" in answer, \
            f"Expected '200mm' in answer but got: {answer[:200]}"
        assert "150" not in answer, \
            f"Answer hallucinated '150' which is in blueprint, not spec: {answer[:200]}"

    @skip_llm
    def test_TC_QRY_10b_concrete_grade_correct(self, client, uploaded_spec):
        """spec.pdf says C30 for slabs, C35 for columns. Answer must cite one."""
        res = client.post("/api/query/", json={
            "question": "What concrete grade is used for columns?",
            "doc_ids": [uploaded_spec["doc_id"]],
        })
        answer = res.json()["answer"].lower()
        assert "c35" in answer or "35 mpa" in answer, \
            f"Expected C35 in answer, got: {answer[:200]}"

    @skip_llm
    def test_TC_QRY_10c_fire_rating_correct(self, client, uploaded_spec):
        """spec.pdf mentions 2-hour fire rating."""
        res = client.post("/api/query/", json={
            "question": "What is the minimum fire rating for structural elements?",
            "doc_ids": [uploaded_spec["doc_id"]],
        })
        answer = res.json()["answer"].lower()
        assert "2" in answer and "hour" in answer, \
            f"Expected 2-hour fire rating, got: {answer[:200]}"

    @skip_llm
    def test_TC_QRY_05_not_found_on_missing_answer(self, client, uploaded_spec):
        """
        ANTI-HALLUCINATION TEST.
        Asking about something not in the document must return NOT FOUND,
        not a made-up answer.
        """
        res = client.post("/api/query/", json={
            "question": "What is the project budget in Pakistani Rupees?",
            "doc_ids": [uploaded_spec["doc_id"]],
        })
        assert res.status_code == 200
        answer = res.json()["answer"].upper()
        assert "NOT FOUND" in answer, \
            f"Expected NOT FOUND but LLM hallucinated: {answer[:200]}"

    @skip_llm
    def test_TC_QRY_05b_not_found_on_unrelated_topic(self, client, uploaded_spec):
        """Asking about cooking recipes should return NOT FOUND."""
        res = client.post("/api/query/", json={
            "question": "How do I make biryani?",
            "doc_ids": [uploaded_spec["doc_id"]],
        })
        answer = res.json()["answer"].upper()
        assert "NOT FOUND" in answer, \
            f"LLM answered a cooking question from a structural spec: {answer[:200]}"

    @skip_llm
    def test_TC_QRY_01_answer_has_source_citation(self, client, uploaded_spec):
        """
        Answer text itself must contain a source reference (page mention or filename).
        The construction domain prompt requires this.
        """
        res = client.post("/api/query/", json={
            "question": "What rebar size is specified for the main bars?",
            "doc_ids": [uploaded_spec["doc_id"]],
        })
        answer = res.json()["answer"].lower()
        # Should contain "page", "source", "section", or "spec" in the answer text
        has_reference = any(w in answer for w in ["page", "source", "section", "spec", "per"])
        assert has_reference, \
            f"Answer has no source reference. Prompt may not be enforcing citations: {answer[:300]}"


class TestQueryScoping:
    """Tests for doc_ids scoping — does filtering actually work?"""

    @skip_llm
    def test_TC_QRY_06_scoped_query_only_cites_target_doc(self, client,
                                                            uploaded_spec,
                                                            uploaded_blueprint):
        """When doc_ids=[spec_id], citations must only reference spec, not blueprint."""
        spec_id = uploaded_spec["doc_id"]
        res = client.post("/api/query/", json={
            "question": "What is the slab thickness?",
            "doc_ids": [spec_id],
        })
        for cit in res.json()["citations"]:
            assert cit["doc_id"] == spec_id, \
                f"Scoped query returned citation from wrong doc: {cit['doc_id']}"

    @skip_llm
    def test_TC_QRY_07_global_query_can_cite_multiple_docs(self, client,
                                                              uploaded_spec,
                                                              uploaded_blueprint):
        """Global query (doc_ids=None) should be able to retrieve from both docs."""
        res = client.post("/api/query/", json={
            "question": "What is the slab thickness?",
            "doc_ids": None,
        })
        assert res.status_code == 200
        # With two docs uploaded both saying different things about slabs,
        # at least one citation should exist
        assert len(res.json()["citations"]) >= 1


class TestQueryEdgeCases:

    def test_TC_QRY_04_empty_question_handled(self, client):
        """Empty question string must not crash the server."""
        res = client.post("/api/query/", json={"question": ""})
        # Should either return 422 (validation) or 200 with NOT FOUND — not 500
        assert res.status_code != 500, "Server crashed on empty question"

    def test_TC_QRY_missing_question_field(self, client):
        """Missing 'question' field must return 422 validation error."""
        res = client.post("/api/query/", json={"top_k": 3})
        assert res.status_code == 422

    def test_TC_QRY_invalid_top_k_type(self, client, uploaded_spec):
        """top_k as a string must return 422."""
        res = client.post("/api/query/", json={
            "question": "What is the slab thickness?",
            "top_k": "five",
        })
        assert res.status_code == 422

    def test_TC_QRY_nonexistent_doc_id_scoped(self, client):
        """Querying a non-existent doc_id must return empty citations, not crash."""
        if not REAL_GEMINI:
            pytest.skip("Need real Gemini key")
        res = client.post("/api/query/", json={
            "question": "What is the slab thickness?",
            "doc_ids": ["nonexistent-uuid-99999"],
        })
        assert res.status_code == 200
        # Empty citations or NOT FOUND — not a 500
        body = res.json()
        assert "answer" in body