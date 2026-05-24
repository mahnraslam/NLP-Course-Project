# ConstructOS — Remaining Tasks (Team of 4)

All scaffold code is written. What remains is integration, testing, and polish.
Each member owns one vertical slice end-to-end.

---

## Member 1 — Backend Core & PDF Pipeline

**Goal:** Make upload → parse → embed → store work reliably.

Tasks:
- [ ] Install system dependency `poppler` locally and verify `pdf2image` works
- [ ] Test `pdf_parser.parse()` on real construction PDFs; handle scanned-only pages (OCR fallback with `pytesseract`)
- [ ] Tune chunk size in `embedder.py` (currently whole page = 1 chunk; split into ~500-token chunks with overlap)
- [ ] Add `GET /documents/{doc_id}/file` endpoint to serve the raw PDF for BlueprintViewer
- [ ] Add `GET /documents/{doc_id}/page/{n}` endpoint to serve PNG page images
- [ ] Write pytest tests for `pdf_parser` and `embedder`

---

## Member 2 — RAG & Gemini Integration

**Goal:** Make Q&A return accurate, well-cited answers.

Tasks:
- [ ] Add your real `GEMINI_API_KEY` to `backend/.env`
- [ ] Test `rag.answer()` end-to-end; tune the prompt in `rag.py` for construction domain
- [ ] Improve citation accuracy: match answer sentences back to source chunks
- [ ] Handle Gemini rate-limit errors (retry with exponential backoff in `gemini.py`)
- [ ] Add `POST /query/vision` endpoint that sends a page image + question to `gemini.generate_with_image()`
- [ ] Write pytest tests for `rag.py` with mocked Gemini responses

---

## Member 3 — Conflict Detection

**Goal:** Make cross-document conflict detection useful and fast.

Tasks:
- [ ] Optimize `conflict.detect()` — current O(n²) chunk comparison is too slow; use vector similarity threshold to pre-filter candidate pairs before calling Gemini
- [ ] Add project-level conflict scan: `POST /conflicts/detect` should accept a project ID and scan all docs in it
- [ ] Parse Gemini's YES/NO response more robustly (regex, not `startswith`)
- [ ] Add a `severity` field to `Conflict` schema (low / medium / high) and have Gemini classify it
- [ ] Write pytest tests for `conflict.py` with mocked Gemini

---

## Member 4 — Frontend Polish & Integration

**Goal:** Make the UI fully functional and usable.

Tasks:
- [ ] Run `npm install` in `frontend/` and verify the dev server starts (`npm run dev`)
- [ ] Wire `Sidebar` to refresh after a new upload in `Dashboard.jsx`
- [ ] Fix `BlueprintViewer`: the `/documents/{docId}/file` URL needs auth-free access; update `client.js` to fetch the PDF blob and pass an object URL to the viewer
- [ ] Add loading spinners and error toasts to `UploadZone`, `ChatPanel`, and `ConflictList`
- [ ] Add a page-count display in `ProjectView` and disable the ▶ button at the last page
- [ ] Style the app with a CSS framework (Tailwind or plain CSS module) — currently unstyled
- [ ] Write basic smoke tests with Vitest + React Testing Library for `ChatPanel` and `UploadZone`

---

## Shared / Final Integration (all 4, last day)

- [ ] Run `docker-compose up` and verify full stack works together
- [ ] Test with 2–3 real construction PDF pairs for conflict detection
- [ ] Write a 1-page `DEMO.md` with setup steps and example queries
- [ ] Record a 3-minute demo video

---

## How to Run Locally (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173
