# ConstructOS MVP

AI Construction Intelligence Platform — Q&A over blueprints, conflict detection, blueprint viewer.

## What makes this different from NotebookLM

| Feature | NotebookLM | ConstructOS |
|---|---|---|
| Q&A over PDF text | ✅ | ✅ |
| Blueprint IMAGE understanding (vision) | ❌ | ✅ Gemini Vision on drawing-heavy pages |
| Cross-doc conflict detection | ❌ | ✅ 10-topic smart approach (not brute force) |
| Click citation → jump to blueprint page | ❌ | ✅ Bidirectional citation UI |
| Construction domain prompt engineering | ❌ | ✅ Structured answers with technical detail |
| Self-hosted, offline-capable | ❌ | ✅ Docker, local ChromaDB |

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- poppler (for blueprint image rendering)
  - Ubuntu/WSL: `sudo apt install poppler-utils`
  - macOS:      `brew install poppler`
  - Windows:    download from https://github.com/oschwartz10612/poppler-windows/releases
- A Gemini API key (free at https://aistudio.google.com)

---

## Setup & Run

### 1. Backend

```bash
cd backend
python -m venv venv
# Windows:  venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt

# Add your Gemini key
echo "GEMINI_API_KEY=your_key_here" > .env
# (other .env values have defaults)

uvicorn main:app --reload --port 8000
```

Backend runs at: http://localhost:8000
API docs at:     http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173

---

## Usage

1. Open http://localhost:5173
2. Upload a construction PDF (blueprint, spec, RFI — any PDF)
3. Select it from the left sidebar → opens Project View
4. **Chat tab**: Ask technical questions → get cited answers
5. **Click a citation page** → automatically jumps to that page in Blueprint tab
6. **Conflicts tab**: Select two documents → detect contradictions in 10 topics

---

## Architecture

```
PDF Upload
  → pdfplumber (text extraction per page)
  → pdf2image (render pages as PNG)
  → Gemini Vision (for drawing-heavy pages < 200 chars text)
  → chunk (1500 chars, 100 overlap)
  → Gemini embed (text-embedding-004, 768-dim)
  → ChromaDB (local persistent vector store)

Q&A Query
  → embed question
  → ChromaDB top-5 retrieval
  → Construction domain prompt → Gemini 2.0 Flash
  → Structured answer + citations with page numbers

Conflict Detection
  → 10 construction topics (slab, rebar, columns, walls, levels…)
  → Per topic: retrieve top-2 from each doc
  → Single LLM call per topic → JSON {conflict, severity, description, quotes}
  → Max 10 LLM calls total (not brute force)
```

---

## Folder Structure

```
constructos/
├── backend/
│   ├── main.py                   # FastAPI app
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env                      # GEMINI_API_KEY goes here
│   ├── routers/
│   │   ├── documents.py          # Upload, list, delete
│   │   ├── query.py              # Q&A endpoint
│   │   └── conflicts.py          # Conflict detection
│   ├── services/
│   │   ├── gemini.py             # Embed, generate, vision
│   │   ├── pdf_parser.py         # Parse + vision enrich
│   │   ├── embedder.py           # Chunk → Gemini embed → store
│   │   ├── vector_store.py       # ChromaDB wrapper
│   │   ├── rag.py                # Construction Q&A with citations
│   │   └── conflict.py           # Smart 10-topic conflict detection
│   ├── models/
│   │   └── schemas.py            # Pydantic models
│   └── storage/
│       ├── uploads/              # Raw PDFs
│       ├── pages/                # PNG renders (served at /pages/...)
│       └── chroma_db/            # Vector index (persisted)
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js            # Proxy: /api and /pages → localhost:8000
    └── src/
        ├── App.jsx
        ├── api/client.js
        ├── components/
        │   ├── Sidebar.jsx       # Doc list with page/chunk counts
        │   ├── UploadZone.jsx    # Drag-drop upload with status
        │   ├── ChatPanel.jsx     # Q&A with suggestion chips
        │   ├── CitationCard.jsx  # Click → jumps blueprint to that page
        │   ├── BlueprintViewer.jsx # PNG page viewer
        │   └── ConflictList.jsx  # Select 2 docs → detect conflicts
        └── pages/
            ├── Dashboard.jsx     # Home with upload
            └── ProjectView.jsx   # 3-tab: Chat / Blueprint / Conflicts
```
