# 📄 Summarix

**Summarix** is a full-stack, AI-powered document summarization and RAG (Retrieval-Augmented Generation) chat application. It supports multiple AI providers — **Google Gemini**, **Groq**, and **Ollama (local)** — with automatic fallback to ensure reliable responses. The app features a modern React frontend with authentication, a sidebar with user profile management, and rich export options.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔐 **Authentication** | Sign up / Log in with persistent sessions (stored in localStorage) |
| 👤 **User Profile** | Sidebar profile section with avatar initials, name, email, and logout |
| 📄 **Single Document Summary** | Upload one PDF, DOCX, or TXT → get a structured AI summary |
| 📚 **Multi-Document Summary** | Upload up to 10 files simultaneously → compare in a results table |
| 🧠 **Three Summary Modes** | Short (3 bullets), Detailed (full paragraph), Academic (formal abstract) |
| 💬 **RAG Document Chat** | Ask questions about your document using FAISS vector search + AI |
| ⬇️ **Export Summaries** | Download single summaries as **PDF**; multi-doc results as **CSV** or **PDF table** |
| ⚡ **Smart Caching** | Previously generated summaries are instantly retrieved from cache |
| 🔄 **AI Fallback Chain** | Gemini → Groq → Ollama (automatic, no manual switching needed) |
| 🛡️ **Upload Size Limit** | Maximum 10 MB per file; maximum 10 files (100 MB total) per request |

---

## 🚀 Tech Stack

### Frontend
- **React 18** + **Vite** + **TypeScript**
- **Tailwind CSS v4** — utility-first styling
- **React Router v6** — client-side routing with protected & guest routes
- **Lucide React** — icon library
- **SF Pro Display** — custom font (loaded via `@font-face`)

### Backend
- **Python 3.10+** + **FastAPI** (v0.115)
- **Uvicorn** — ASGI server
- **Google Gemini** (`gemini-2.0-flash`) — primary AI model
- **Groq** — secondary AI fallback
- **Ollama** (`llama3.2`) — local AI fallback (offline, zero API limits)
- **FAISS** — in-memory vector database for RAG
- **Sentence Transformers** — local document embeddings (no API)
- **ReportLab** — PDF generation
- **PyPDF + python-docx** — document parsing

---

## 📁 Project Structure

```text
document_summarizer/
├── backend/                        # FastAPI backend
│   ├── main.py                     # App entry point, CORS, middleware
│   ├── config.py                   # Settings & environment variables
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # API keys (not committed)
│   ├── routers/
│   │   ├── summarize.py            # POST /api/v1/summarize (single & multi)
│   │   ├── download.py             # POST /api/v1/download/{pdf,csv,table-pdf}
│   │   └── chat.py                 # POST /api/v1/chat/{ingest,ask}
│   ├── services/
│   │   ├── ai_client.py            # Gemini / Groq / Ollama with fallback logic
│   │   ├── summarizer.py           # Prompt building & summary parsing
│   │   ├── rag_service.py          # FAISS ingestion & retrieval
│   │   ├── file_parser.py          # PDF / DOCX / TXT text extraction
│   │   ├── cache_service.py        # In-memory summary cache
│   │   ├── pdf_generator.py        # ReportLab PDF export
│   │   └── csv_generator.py        # CSV export
│   └── models/
│       └── schemas.py              # Pydantic request/response models
│
└── frontend/                       # React frontend
    ├── src/
    │   ├── App.tsx                  # Router setup, protected & guest routes
    │   ├── main.tsx                 # React entry point
    │   ├── index.css                # Tailwind base + custom font + animations
    │   ├── contexts/
    │   │   ├── AuthContext.tsx      # Auth state (login, signup, logout)
    │   │   └── ToastContext.tsx     # Global toast notifications
    │   ├── components/
    │   │   ├── Layout.tsx           # Sidebar nav + profile section
    │   │   ├── FileUpload.tsx       # Drag-and-drop file uploader
    │   │   ├── SummaryCard.tsx      # Single document result card
    │   │   └── ResultsTable.tsx     # Multi-document results table
    │   └── pages/
    │       ├── Login.tsx            # Sign-in page
    │       ├── Signup.tsx           # Registration page
    │       ├── Home.tsx             # Upload & summarize page
    │       ├── Summary.tsx          # View latest summary
    │       ├── Documents.tsx        # Documents list
    │       └── Chat.tsx             # RAG chat interface
    ├── public/
    │   └── fonts/                   # SF Pro Display font files
    └── package.json
```

---

## 🔧 Installation & Setup

### Prerequisites
- **Node.js** 18+ and **npm**
- **Python** 3.10+
- *(Optional)* **Ollama** for fully local/offline mode

---

### 1. Backend Setup

```bash
cd backend

# Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory with your API keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

> **Note:** Both keys are optional. If Gemini fails, the app automatically falls back to Groq, then to Ollama (if running locally). At least one should be configured for cloud usage.

Start the FastAPI server:

```bash
venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive API docs: `http://localhost:8000/docs`

---

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The web app will be available at `http://localhost:5173`.

---

### 3. (Optional) Local AI with Ollama

To use the fully offline fallback:

1. Download Ollama from [ollama.com](https://ollama.com)
2. Pull the model:
   ```bash
   ollama pull llama3.2
   ```
3. Ensure it's running: `ollama serve`

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/summarize` | Summarize a single document |
| `POST` | `/api/v1/summarize-multiple` | Summarize up to 10 documents |
| `POST` | `/api/v1/download/pdf` | Export single summary as PDF |
| `POST` | `/api/v1/download/csv` | Export multi-doc results as CSV |
| `POST` | `/api/v1/download/table-pdf` | Export multi-doc results as PDF table |
| `POST` | `/api/v1/chat/ingest` | Ingest a document into the vector store |
| `POST` | `/api/v1/chat/ask` | Ask a question about an ingested document |
| `GET` | `/api/v1/chat/documents` | List all ingested documents |
| `DELETE` | `/api/v1/chat/documents/{id}` | Remove a document from vector store |
| `GET` | `/cache/stats` | View summary cache statistics |
| `DELETE` | `/cache/clear` | Clear all cached summaries |

---

## 📝 Supported File Types

| Format | Extension | Max Size |
|---|---|---|
| PDF | `.pdf` | 10 MB |
| Word Document | `.docx` | 10 MB |
| Plain Text | `.txt` | 10 MB |

> Maximum **10 files** per multi-document request (100 MB total).

---

## 🔒 Security Notes

- Never commit `.env` files to source control.
- Add `backend/.env`, `backend/venv/`, and `frontend/node_modules/` to `.gitignore`.
- API keys should always be kept private.
- User credentials are stored in browser `localStorage` — this is a demo setup. For production, replace with a proper backend auth system (JWT, OAuth, etc.).

---

## 🤖 AI Model Priority

The backend uses an automatic fallback chain:

```
Google Gemini (gemini-2.0-flash)
        ↓ (if unavailable / quota exceeded)
Groq (fast inference)
        ↓ (if unavailable)
Ollama (llama3.2 — fully local, no internet required)
```

---

*Built with FastAPI + React + Gemini + Groq + Ollama + FAISS*
