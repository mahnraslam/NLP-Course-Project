from pydantic import BaseModel
from typing import List, Optional

# ── Documents ────────────────────────────────────────────────────────────────
class DocumentMeta(BaseModel):
    doc_id: str
    filename: str
    page_count: int = 0
    chunk_count: int = 0
    doc_type: str = "other"

class DeleteResponse(BaseModel):
    doc_id: str
    deleted: bool

# ── Q&A ──────────────────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str
    doc_ids: Optional[List[str]] = None
    top_k: int = 5

class Citation(BaseModel):
    doc_id: str
    filename: str
    page_num: int
    chunk_text: str
    relevance_score: float = 0.0

class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: List[Citation]

# ── Conflicts ────────────────────────────────────────────────────────────────
class ConflictRequest(BaseModel):
    doc_id_a: str
    doc_id_b: str
    filename_a: str = ""
    filename_b: str = ""

class ConflictItem(BaseModel):
    severity: str          # "high" | "medium" | "low"
    topic: str
    description: str
    quote_a: str
    quote_b: str
    page_a: int
    page_b: int
    filename_a: str
    filename_b: str

class ConflictResponse(BaseModel):
    doc_id_a: str
    doc_id_b: str
    conflicts: List[ConflictItem]
    total: int

class AllConflictsRequest(BaseModel):
    doc_ids: List[str]

class AllConflictsResponse(BaseModel):
    conflicts: List[ConflictItem]
    total: int
