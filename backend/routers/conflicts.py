from fastapi import APIRouter
from models.schemas import ConflictRequest, ConflictResponse
from services.conflict import detect

router = APIRouter()

@router.post("/detect", response_model=ConflictResponse)
async def detect_conflicts(req: ConflictRequest):
    return detect(req.doc_id_a, req.doc_id_b, req.filename_a, req.filename_b)
