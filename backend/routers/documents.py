import os, uuid, shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.pdf_parser import parse_pdf
from services.embedder import embed_and_store
from services import vector_store
from models.schemas import DocumentMeta, DeleteResponse
from dotenv import load_dotenv

load_dotenv()
router     = APIRouter()
UPLOAD_DIR = os.getenv("UPLOAD_PATH", "storage/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=DocumentMeta)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files supported.")
    doc_id = str(uuid.uuid4())
    dest   = os.path.join(UPLOAD_DIR, f"{doc_id}_{file.filename}")
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        chunks, page_count = parse_pdf(dest, doc_id)
    except Exception as e:
        os.remove(dest)
        raise HTTPException(500, f"PDF parsing failed: {e}")
    if not chunks:
        raise HTTPException(422, "No readable content found in PDF.")
    embed_and_store(chunks, doc_id, file.filename)
    return DocumentMeta(doc_id=doc_id, filename=file.filename,
                        page_count=page_count, chunk_count=len(chunks))

@router.get("/", response_model=list[DocumentMeta])
def list_documents():
    return vector_store.list_documents()

@router.delete("/{doc_id}", response_model=DeleteResponse)
def delete_document(doc_id: str):
    vector_store.delete_document(doc_id)
    return DeleteResponse(doc_id=doc_id, deleted=True)

@router.get("/{doc_id}/page-url/{page_num}")
def page_url(doc_id: str, page_num: int):
    pages_path = os.getenv("PAGES_PATH", "storage/pages")
    path = os.path.join(pages_path, doc_id, f"page_{page_num}.png")
    return {"exists": os.path.isfile(path),
            "url": f"/pages/{doc_id}/page_{page_num}.png"}
