 

from fastapi import APIRouter
from models.schemas import QueryRequest, QueryResponse
from services.rag import answer

router = APIRouter()

@router.post("/", response_model=QueryResponse)
async def query(req: QueryRequest):
    """
    Answer a question about uploaded construction documents.

    Set visual=true in the request body to enable multimodal mode:
    the top retrieved page images are sent to Gemini Vision alongside
    the extracted text so the model can actually *see* the drawings.
    """
    return answer(req.question, req.doc_ids, req.top_k, req.visual)
 

 