
# CyberGuard AI — Cybersecurity RAG Chatbot 🛡️

**CyberGuard AI** is a learning-first cybersecurity chatbot. It’s built for people who want to learn security but can’t find enough reliable material—or hit generic chatbot limits—and for learners who prefer concise explanations over reading long books.  
It lets you **load your own PDFs/notes** and trusted public resources, builds a **searchable vector knowledge base (Chroma)**, and answers in plain language with **source citations**. It runs with **free/local LLM backends** (Ollama / HF Inference / local transformers) and falls back to a safe template when no model is available.  
**Strictly defensive and educational**: the assistant focuses on best practices, concepts, and safe workflows—not step-by-step exploit instructions.

It ingests documents, embeds them into a vector database (Chroma by default), and answers questions with multiple **free LLM backends** (Ollama, Hugging Face Inference API, or local transformers), with a template fallback.

---

## Repository Layout (current)

```
.
├─ README.md
├─ .env
├─ backend/
│  ├─ __init__.py
│  ├─ main.py                 # FastAPI app (lifespan startup, endpoints)
│  ├─ document_loader.py      # Async ingestion (PDF/TXT/others) + chunking
│  ├─ rag_service.py          # RAG pipeline + LLM backends + retrieval
│  ├─ vector_db.py            # Chroma / Pinecone adapters + config + health
│  ├─ requirements.txt
├─ data/                      # (used by backend) raw docs and temp uploads
│  └─ raw_documents/          # Pre-load folder processed on startup
└─ frontend/
   ├─ UI.py                   # Streamlit app (chat, upload, search, admin)
   └─ requirements.txt
```

> **Where files are read/written**
- Backend pre-loads documents from `./data/raw_documents/` on startup and saves temporary uploads to `./data/temp/`.
- Chroma persistence directory defaults to `./vector_store/chroma_db` (see `vector_db_config.json` auto-created on first run).

---

## Features

- 🔎 **Document ingestion**: async parsing with paragraph + overlapping chunking; supports `.txt`, `.pdf`, `.md`, `.csv`, `.json`, `.xml`.
- 🧠 **Embeddings**: `sentence-transformers` **all-MiniLM-L6-v2**.
- 🗃️ **Vector DB**: Chroma (local, persistent). Pinecone optional.
- 💬 **LLM backends (auto-detect order)**: Ollama → HF Inference API → local transformers (CPU/GPU) → template fallback.
- 🧪 **Health & stats** endpoints; **search-only** endpoint; **admin** endpoint for bulk processing.
- 🎛️ **Streamlit UI**: cyberpunk theme, chat with sources, upload docs, search, basic admin panel.

---

## Requirements

- Python **3.10+**
- (Optional) **Ollama** for free, local LLMs (e.g., `llama2:7b-chat`, `mistral:7b`)
- (Optional) **Pinecone** account if you switch from Chroma
- (Optional) **CUDA** for local GPU inference

> Use a virtual environment. On Windows, activate via `.venv\Scripts\activate`.

---

## Environment Variables (`.env` at repo root)

```env
# Optional: Hugging Face Inference API
HUGGINGFACE_TOKEN=hf_xxx

# Optional: Pinecone
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=

# CORS for the UI
ALLOWED_ORIGINS=http://localhost:8501,http://127.0.0.1:8501
```

The vector DB config file **`vector_db_config.json`** will be created automatically with defaults:
- default DB: `chromadb`
- persist dir: `./vector_store/chroma_db`
- collection: `cybersec_docs`

---

## Setup & Run

### 1) Backend (FastAPI)
```bash
# from repo root
python -m venv .venv
# Linux/Mac
source .venv/bin/activate
# Windows
# .venv\Scripts\activate

pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
# Swagger docs: http://127.0.0.1:8000/docs
```

On first run, the backend will:
1. Initialize Chroma (or Pinecone if configured).
2. Load the embedding model **all-MiniLM-L6-v2**.
3. Auto-detect an LLM backend (Ollama → HF → local → template).
4. Process any files found in `./data/raw_documents/`.

> **Tip:** Place test files in `data/raw_documents/` before starting to see immediate results.

### 2) Frontend (Streamlit)
```bash
# in another terminal (same or another venv)
pip install -r frontend/requirements.txt
streamlit run frontend/UI.py
# UI default: http://localhost:8501
```
Ensure `API_BASE_URL` inside `frontend/UI.py` points to the running backend (default `http://127.0.0.1:8000`).

---

## API Endpoints (summary)

**Public**
- `GET /` — root info
- `GET /health` — service + DB status (includes uptime)
- `GET /stats` — counts, backend info
- `POST /chat` — body:
  ```json
  {
    "message": "What is CVE-2023-XXXXX?",
    "session_id": "optional-uuid",
    "include_sources": true,
    "max_sources": 3
  }
  ```
- `POST /upload-document` — multipart file; validates type/size (≤10MB)
- `POST /upload-text` — JSON `{ filename, content, document_type?, metadata? }`
- `GET /search?query=...&top_k=5` — retrieval only (no generation)
- `DELETE /documents/{document_id}` — remove by ID (vector DB)

**Admin**
- `POST /admin/process-documents` — bulk process `./data/raw_documents/`

> The Streamlit **Admin** tab references `/admin/export-data` and `/admin/clear-database` for convenience, but these handlers are **not implemented** yet in `backend/main.py`. Add them or hide those UI controls if not needed.

---

## RAG Pipeline (high level)

1. **Ingestion** (`document_loader.py`)
   - Detects type → reads (PDF via PyPDF2) → chunks by paragraph then by size (`chunk_size=1000`, `overlap≈200` words).

2. **Embeddings**
   - `SentenceTransformer('all-MiniLM-L6-v2')` encodes chunks.

3. **Store / Search** (`vector_db.py`)
   - **Chroma**: persistent client, cosine distance; stores docs + metadata.
   - Search returns docs + distances; converted to similarity scores.

4. **Answering** (`rag_service.py`)
   - Retrieve top-k → simple redundancy filter (Jaccard threshold `0.8`) → construct concise prompt → generate via chosen LLM backend.
   - Backends:
     - **Ollama**: `POST /api/generate` to `localhost:11434` (model auto-picked if present).
     - **HF Inference API**: default `microsoft/DialoGPT-medium` (example, free-tier).
     - **Local transformers**: `microsoft/DialoGPT-small` pipeline.
     - **Template fallback**: keyword-based concise summary when no LLM is available.

---

## Streamlit UI (features)

- **Chat Analysis** tab: ask questions, view sources/snippets and timings.
- **Upload Intel** tab: file or text ingestion; shows chunks created and timings.
- **Threat Search** tab: search-only workflow with previews.
- **Admin Panel**: bulk process folder; (export & clear are placeholders unless implemented).

---

## Ollama Quick Start (optional but recommended)

```bash
# Install Ollama (https://ollama.com/)
ollama serve &
ollama pull llama2:7b-chat   # or mistral:7b
# restart backend so rag_service auto-detects Ollama
```

---

## Troubleshooting

- **UI says SYSTEM OFFLINE** → backend not running / CORS mismatch. Check `ALLOWED_ORIGINS` and `API_BASE_URL`.
- **No answers / “not enough information”** → ingest documents first (Upload tab or put files in `data/raw_documents/`).
- **PDFs parse empty** → ensure `PyPDF2` is installed; image-only PDFs won’t extract text.
- **Chroma errors** → delete `./vector_store/chroma_db` if corrupted and restart.
- **HF 401** → set a valid `HUGGINGFACE_TOKEN` or switch to Ollama/local.
- **Admin export/clear buttons** → not implemented server-side; add endpoints or hide buttons.

---

## Roadmap / TODO

- [ ] Implement `/admin/export-data` (return JSON of stored docs & metadata).
- [ ] Implement `/admin/clear-database` (drop collection/reset Chroma dir).
- [ ] Add reranking stage (e.g., bge-reranker or Cohere Rerank).
- [ ] Per-session memory & chat history store.
- [ ] Dockerfiles for backend/frontend + `docker-compose.yml`.
- [ ] Tests (`pytest`) for ingestion, search, and chat.

---

## License

MIT (update if needed).

## Acknowledgments
Thanks to the authors of FastAPI, Streamlit, Sentence-Transformers, and Chroma.

## Running with `start.bat`  
For convenience, a **`start.bat`** file is included at the root of the project.  
Double‑clicking this file will automatically start the backend (FastAPI) and frontend (Streamlit) together, so you don’t need to run separate commands manually.


## Demo & Presentation  
You can find the demo video and presentation here:  
📂 [Google Drive Folder](https://drive.google.com/drive/folders/1mu_DQivUphgDBEtQbv_YxJy2gPIRkEQY?usp=sharing)