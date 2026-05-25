from fastapi import APIRouter
from models.schemas import ConflictRequest, ConflictResponse, AllConflictsRequest, AllConflictsResponse
from services.conflict import detect, detect_all_conflicts

router = APIRouter()

@router.post("/detect", response_model=ConflictResponse)
async def detect_conflicts(req: ConflictRequest):
    return detect(req.doc_id_a, req.doc_id_b, req.filename_a, req.filename_b)

@router.post("/detect-all", response_model=AllConflictsResponse)
async def detect_all(req: AllConflictsRequest):
    conflicts = detect_all_conflicts(req.doc_ids)
    return AllConflictsResponse(conflicts=conflicts, total=len(conflicts))
