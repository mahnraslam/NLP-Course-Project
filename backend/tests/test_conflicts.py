"""
test_conflicts.py — QA tests for /api/conflicts/detect endpoint.

Seeded conflicts between spec.pdf and blueprint.pdf:
  CONFLICT 1: Slab thickness — spec=200mm, blueprint=150mm  → HIGH severity
  CONFLICT 2: Column size    — spec=400x400, blueprint=300x300 → HIGH severity

Covers:
  TC-CON-01  Detect conflicts between two docs → returns ConflictResponse
  TC-CON-02  At least 1 of 2 seeded conflicts detected (recall >= 50%)
  TC-CON-03  Both seeded conflicts detected (recall = 100%)
  TC-CON-04  Severity field is valid value (high/medium/low)
  TC-CON-05  Each conflict has quote_a, quote_b, page_a, page_b
  TC-CON-06  Same doc vs same doc → 0 conflicts (no false positives)
  TC-CON-07  Missing doc_id_a or doc_id_b → 422 validation error
  TC-CON-08  Both docs with no overlapping topics → 0 conflicts
  TC-CON-09  total field equals len(conflicts)
  TC-CON-10  Response reflects correct doc_id_a, doc_id_b
"""
import os
import pytest

REAL_GEMINI = os.environ.get("GEMINI_API_KEY", "test-key") != "test-key"
skip_llm = pytest.mark.skipif(not REAL_GEMINI, reason="Real GEMINI_API_KEY required")

VALID_SEVERITIES = {"high", "medium", "low"}


class TestConflictStructure:

    @skip_llm
    def test_TC_CON_01_response_schema(self, client, uploaded_spec, uploaded_blueprint):
        """Conflict response must have doc_id_a, doc_id_b, conflicts, total."""
        res = client.post("/api/conflicts/detect", json={
            "doc_id_a":   uploaded_spec["doc_id"],
            "doc_id_b":   uploaded_blueprint["doc_id"],
            "filename_a": "spec.pdf",
            "filename_b": "blueprint.pdf",
        })
        assert res.status_code == 200
        body = res.json()
        assert "doc_id_a"  in body
        assert "doc_id_b"  in body
        assert "conflicts" in body
        assert "total"     in body
        assert isinstance(body["conflicts"], list)
        assert isinstance(body["total"], int)

    @skip_llm
    def test_TC_CON_10_response_reflects_correct_ids(self, client,
                                                       uploaded_spec,
                                                       uploaded_blueprint):
        """doc_id_a and doc_id_b in response must match what was sent."""
        spec_id = uploaded_spec["doc_id"]
        bp_id   = uploaded_blueprint["doc_id"]
        res = client.post("/api/conflicts/detect", json={
            "doc_id_a": spec_id,
            "doc_id_b": bp_id,
        })
        body = res.json()
        assert body["doc_id_a"] == spec_id
        assert body["doc_id_b"] == bp_id

    @skip_llm
    def test_TC_CON_09_total_matches_conflicts_length(self, client,
                                                        uploaded_spec,
                                                        uploaded_blueprint):
        """total field must equal len(conflicts)."""
        res = client.post("/api/conflicts/detect", json={
            "doc_id_a": uploaded_spec["doc_id"],
            "doc_id_b": uploaded_blueprint["doc_id"],
        })
        body = res.json()
        assert body["total"] == len(body["conflicts"]), \
            f"total={body['total']} but conflicts has {len(body['conflicts'])} items"

    @skip_llm
    def test_TC_CON_04_severity_valid_values(self, client,
                                               uploaded_spec,
                                               uploaded_blueprint):
        """Every conflict item must have severity in {high, medium, low}."""
        res = client.post("/api/conflicts/detect", json={
            "doc_id_a": uploaded_spec["doc_id"],
            "doc_id_b": uploaded_blueprint["doc_id"],
        })
        for item in res.json()["conflicts"]:
            assert item["severity"] in VALID_SEVERITIES, \
                f"Invalid severity: {item['severity']}"

    @skip_llm
    def test_TC_CON_05_conflict_items_have_required_fields(self, client,
                                                             uploaded_spec,
                                                             uploaded_blueprint):
        """Every conflict item must have quote_a, quote_b, page_a, page_b, description."""
        res = client.post("/api/conflicts/detect", json={
            "doc_id_a":   uploaded_spec["doc_id"],
            "doc_id_b":   uploaded_blueprint["doc_id"],
            "filename_a": "spec.pdf",
            "filename_b": "blueprint.pdf",
        })
        for item in res.json()["conflicts"]:
            assert "quote_a"     in item and item["quote_a"],     "Missing quote_a"
            assert "quote_b"     in item and item["quote_b"],     "Missing quote_b"
            assert "page_a"      in item and item["page_a"] >= 1, "Invalid page_a"
            assert "page_b"      in item and item["page_b"] >= 1, "Invalid page_b"
            assert "description" in item and item["description"], "Missing description"
            assert "topic"       in item and item["topic"],       "Missing topic"


class TestConflictDetectionAccuracy:
    """Tests that verify the AI actually finds the seeded conflicts."""

    @skip_llm
    def test_TC_CON_02_at_least_one_seeded_conflict_found(self, client,
                                                             uploaded_spec,
                                                             uploaded_blueprint):
        """
        RECALL TEST (minimum bar).
        spec.pdf vs blueprint.pdf has 2 seeded conflicts.
        Must find at least 1. Recall >= 50%.
        """
        res = client.post("/api/conflicts/detect", json={
            "doc_id_a":   uploaded_spec["doc_id"],
            "doc_id_b":   uploaded_blueprint["doc_id"],
            "filename_a": "spec.pdf",
            "filename_b": "blueprint.pdf",
        })
        conflicts = res.json()["conflicts"]
        assert len(conflicts) >= 1, \
            f"Expected at least 1 conflict, found 0. Seeded: slab(200 vs 150), column(400x400 vs 300x300)"

    @skip_llm
    def test_TC_CON_03_slab_conflict_detected(self, client,
                                                uploaded_spec,
                                                uploaded_blueprint):
        """
        SPECIFIC CONFLICT TEST.
        Slab thickness: spec=200mm, blueprint=150mm.
        At least one conflict description must mention slab or thickness.
        """
        res = client.post("/api/conflicts/detect", json={
            "doc_id_a":   uploaded_spec["doc_id"],
            "doc_id_b":   uploaded_blueprint["doc_id"],
            "filename_a": "spec.pdf",
            "filename_b": "blueprint.pdf",
        })
        conflicts = res.json()["conflicts"]
        descriptions = " ".join(c["description"].lower() for c in conflicts)
        quotes       = " ".join((c["quote_a"] + c["quote_b"]).lower() for c in conflicts)
        combined     = descriptions + " " + quotes

        slab_found = any(w in combined for w in ["slab", "thickness", "200", "150"])
        assert slab_found, \
            f"Slab conflict (200mm vs 150mm) not detected. Descriptions: {descriptions[:300]}"

    @skip_llm
    def test_TC_CON_03b_column_conflict_detected(self, client,
                                                   uploaded_spec,
                                                   uploaded_blueprint):
        """
        Column size: spec=400x400, blueprint=300x300.
        At least one conflict must mention column dimensions.
        """
        res = client.post("/api/conflicts/detect", json={
            "doc_id_a":   uploaded_spec["doc_id"],
            "doc_id_b":   uploaded_blueprint["doc_id"],
            "filename_a": "spec.pdf",
            "filename_b": "blueprint.pdf",
        })
        conflicts = res.json()["conflicts"]
        combined  = " ".join(
            c["description"].lower() + c["quote_a"].lower() + c["quote_b"].lower()
            for c in conflicts
        )
        column_found = any(w in combined for w in ["column", "400", "300"])
        assert column_found, \
            f"Column conflict (400x400 vs 300x300) not detected. Got: {combined[:300]}"

    @skip_llm
    def test_TC_CON_06_same_doc_no_conflicts(self, client, uploaded_spec):
        """
        FALSE POSITIVE TEST.
        Comparing a doc against itself must return 0 conflicts.
        """
        spec_id = uploaded_spec["doc_id"]
        res = client.post("/api/conflicts/detect", json={
            "doc_id_a":   spec_id,
            "doc_id_b":   spec_id,
            "filename_a": "spec.pdf",
            "filename_b": "spec.pdf",
        })
        assert res.status_code == 200
        conflicts = res.json()["conflicts"]
        assert len(conflicts) == 0, \
            f"False positive: {len(conflicts)} conflicts found in same doc vs itself"


class TestConflictValidation:

    def test_TC_CON_07_missing_doc_id_a(self, client):
        """Request without doc_id_a must return 422."""
        res = client.post("/api/conflicts/detect", json={
            "doc_id_b": "some-id",
        })
        assert res.status_code == 422

    def test_TC_CON_07b_missing_doc_id_b(self, client):
        """Request without doc_id_b must return 422."""
        res = client.post("/api/conflicts/detect", json={
            "doc_id_a": "some-id",
        })
        assert res.status_code == 422

    def test_TC_CON_07c_empty_body(self, client):
        """Empty body must return 422."""
        res = client.post("/api/conflicts/detect", json={})
        assert res.status_code == 422

    @skip_llm
    def test_TC_CON_08_nonexistent_ids_return_zero_conflicts(self, client):
        """Non-existent doc IDs produce 0 conflicts (nothing to retrieve)."""
        res = client.post("/api/conflicts/detect", json={
            "doc_id_a": "fake-id-aaa-111",
            "doc_id_b": "fake-id-bbb-222",
        })
        assert res.status_code == 200
        assert res.json()["total"] == 0