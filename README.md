# DocQuery — Retrieval-Augmented Document Q&A Platform

A Retrieval-Augmented Generation (RAG) platform that lets users upload their own documents (PDF, DOCX, TXT) and ask natural-language questions about them — with answers grounded strictly in the uploaded content, not the LLM's general knowledge.

Built to explore production-style RAG architecture: hybrid retrieval, re-ranking, confidence-gated generation, and multi-user isolation — not just a single-file notebook demo.

---

## ✨ Features

- 🔐 **JWT Authentication** — secure signup/login, every request scoped to the authenticated user
- 📄 **Multi-document upload** — supports PDF, DOCX, and TXT, with per-user isolated storage
- 🔍 **Hybrid Retrieval Pipeline** — combines FAISS dense vector search (semantic meaning) with BM25 keyword search (exact term matching)
- 🎯 **Cross-Encoder Re-ranking** — a second-pass model re-scores top candidates for higher precision before generation
- 🚫 **Confidence-gated responses** — the system explicitly refuses to answer when retrieved context is insufficient, instead of hallucinating
- 💬 **Persistent chat sessions** — ChatGPT-style chat threads per document, full history saved per user
- ⚡ **Groq API** — fast, low-latency LLM inference (Llama 3.3, free tier)
- 🐳 **Dockerized** — one-command deployment of the full stack (API + PostgreSQL)

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | FastAPI |
| Database | PostgreSQL + SQLAlchemy ORM |
| Authentication | JWT (python-jose), bcrypt password hashing |
| Vector Search | FAISS (sentence-transformers embeddings) |
| Keyword Search | BM25 (rank-bm25) |
| Re-ranking | Cross-Encoder (sentence-transformers) |
| LLM Inference | Groq API (Llama 3.3 70B) |
| Frontend | HTML + Tailwind CSS + Vanilla JavaScript |
| Deployment | Docker + Docker Compose |

---

## 🏗️ Architecture

```
User uploads document (PDF/DOCX/TXT)
        │
        ▼
Text extraction → Chunking (page-aware)
        │
        ▼
Embeddings generated → stored in FAISS + BM25 index
        │
        ▼
User asks a question (within a chat session)
        │
        ▼
Hybrid Search (FAISS + BM25) → top candidates
        │
        ▼
Cross-Encoder Re-ranking → best chunks selected
        │
        ▼
Confidence check → insufficient? return "I don't know"
        │                              │
        ▼                              
Groq LLM generates grounded answer
        │
        ▼
Saved to PostgreSQL chat history → returned to user
```

---

## 📸 Screenshots


### Login Page

![Login](screenshots/login.png)

### Chat Page
![Chat](screenshots/chat.png)


---

## 🚀 Getting Started

### Option 1: Run with Docker (recommended)

**Prerequisites:** Docker Desktop installed, a free [Groq API key](https://console.groq.com)

1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/ai-tutor-rag-platform.git
cd ai-tutor-rag-platform
```

2. Create a `.env` file in the project root:
```
DATABASE_URL=postgresql://postgres:postgres@db:5432/ai_tutor_db
SECRET_KEY=your_random_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

3. Run everything with one command:
```bash
docker-compose up --build
```

4. Open the API docs: `http://127.0.0.1:8000/docs`
5. Open `frontend/index.html` in your browser to use the UI

---

### Option 2: Run locally (without Docker)

**Prerequisites:** Python 3.11+, PostgreSQL installed locally

1. Clone the repo and create a virtual environment
```bash
git clone https://github.com/YOUR_USERNAME/ai-tutor-rag-platform.git
cd ai-tutor-rag-platform
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Create a PostgreSQL database named `ai_tutor_db`

4. Create a `.env` file (see above), with `DATABASE_URL` pointing to `localhost` instead of `db`:
```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/ai_tutor_db
```

5. Create the database tables
```bash
python create_tables.py
```

6. Run the server
```bash
uvicorn app.main:app --reload
```

7. Open `http://127.0.0.1:8000/docs` or `frontend/index.html`

---

## 📡 API Overview

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/signup` | Register a new user |
| POST | `/auth/login` | Log in, receive a JWT token |
| GET | `/auth/me` | Get current logged-in user info |
| POST | `/documents/upload` | Upload a document (PDF/DOCX/TXT) |
| GET | `/documents/` | List current user's documents |
| DELETE | `/documents/{document_id}` | Delete a document |
| POST | `/chat/sessions` | Create a new chat session for a document |
| GET | `/chat/sessions/{document_id}` | List chat sessions for a document |
| POST | `/chat/ask` | Ask a question within a chat session |
| GET | `/chat/sessions/{session_id}/messages` | Get full chat history for a session |

Full interactive documentation available at `/docs` once running.

---

## 🔮 Future Improvements

- **Multi-document chats** — currently each chat session is scoped to a single document for retrieval accuracy; could be extended with a join table to allow querying across multiple documents in one conversation
- **Refresh token flow** — currently uses long-lived access tokens; a short-lived access token + refresh token pattern would be more production-appropriate
- **Streaming responses** — stream LLM output token-by-token instead of waiting for the full response
- **Support for `.pptx` and legacy `.doc` files**
- **Migration tooling (Alembic)** instead of manual table recreation during schema changes

---

## 👤 Author

Built by [Amritha Dileep Kumar] as a portfolio project demonstrating end-to-end RAG system design, from retrieval engineering to deployment.
