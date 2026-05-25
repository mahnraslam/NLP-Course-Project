import os, uuid, shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services.pdf_parser import parse
from services.embedder import embed_and_store
from services import vector_store
from models.schemas import DocumentMeta, DeleteResponse
from dotenv import load_dotenv

load_dotenv()
router     = APIRouter()
UPLOAD_DIR = os.getenv("UPLOAD_PATH", "storage/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

DOC_TYPES = {"blueprint", "specification", "submittal", "rfi", "om_manual", "other"}

def detect_doc_type(filename: str) -> str:
    name = filename.lower()
    if any(x in name for x in ["dwg", "drawing", "blueprint", "plan", "sheet"]):
        return "blueprint"
    if any(x in name for x in ["spec", "specification", "csi"]):
        return "specification"
    if any(x in name for x in ["submittal", "approval", "shop drawing"]):
        return "submittal"
    if any(x in name for x in ["rfi", "request for information"]):
        return "rfi"
    if any(x in name for x in ["o&m", "manual", "maintenance"]):
        return "om_manual"
    return "other"

@router.post("/upload", response_model=DocumentMeta)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(default=""),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files supported.")
    resolved_type = doc_type if doc_type in DOC_TYPES else detect_doc_type(file.filename)
    doc_id = str(uuid.uuid4())
    dest   = os.path.join(UPLOAD_DIR, f"{doc_id}_{file.filename}")
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        chunks, page_count = parse(dest, doc_id)
    except Exception as e:
        os.remove(dest)
        raise HTTPException(500, f"PDF parsing failed: {e}")
    if not chunks:
        raise HTTPException(422, "No readable content found in PDF.")
    embed_and_store(chunks, doc_id, file.filename, resolved_type)
    return DocumentMeta(doc_id=doc_id, filename=file.filename,
                        page_count=page_count, chunk_count=len(chunks),
                        doc_type=resolved_type)

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
    path = os.path.join(pages_path, f"{doc_id}_page_{page_num}.png")
    return {"exists": os.path.isfile(path),
            "url": f"/pages/{doc_id}_page_{page_num}.png"}
