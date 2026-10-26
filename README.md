# DocQuery — RAG-Based Document Q&A Platform

DocQuery is a document question-answering platform built using Retrieval-Augmented Generation (RAG). Users can upload PDF, DOCX, and TXT files and ask questions about their content. The system retrieves relevant information from the uploaded documents and uses it to generate answers.

The goal of this project is to explore how RAG works in a practical application, from document processing and retrieval to API development, authentication, and automated testing.

## ✨ Features

- 🔐 JWT-based user authentication
- 📄 Upload and manage PDF, DOCX, and TXT documents
- 🔍 Hybrid search using FAISS and BM25
- 🎯 Cross-encoder reranking for more relevant results
- 🤖 Context-based answer generation using the Groq API
- 💬 Persistent chat sessions and conversation history
- 🗄️ PostgreSQL database with SQLAlchemy
- 🐳 Docker and Docker Compose support
- 🧪 Automated tests using pytest
- 🔄 GitHub Actions CI with Ruff and pytest

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Backend | FastAPI, Python |
| Database | PostgreSQL, SQLAlchemy |
| Authentication | JWT, bcrypt |
| Embeddings | Sentence Transformers |
| Retrieval | FAISS, BM25 |
| Reranking | Cross-Encoder |
| LLM | Groq API |
| Testing | pytest, HTTPX |
| Code Quality | Ruff |
| Deployment | Docker, Docker Compose |

## 🏗️ How It Works

1. Users upload a document.
2. The application extracts the text and splits it into chunks.
3. Embeddings and keyword indexes are created for retrieval.
4. When a user asks a question, FAISS and BM25 retrieve relevant chunks.
5. A cross-encoder reranks the results.
6. The retrieved context is passed to the LLM to generate an answer.
7. Chat history is saved in the database.

The system is designed to avoid unsupported answers when the retrieved context is insufficient.

## 🚀 Getting Started

### Prerequisites

- Python 3.12
- Docker Desktop (for Docker setup)
- A Groq API key from the [Groq Console](https://console.groq.com/)

### Run with Docker

Clone the repository:

```bash
git clone https://github.com/Amritha217/DocQuery_RAG_Platform.git
cd DocQuery_RAG_Platform
```

Create a `.env` file in the project root with the environment variables required by your Docker configuration, including your database URL, secret key, and Groq API key.

Then start the application:

```bash
docker compose up --build
```

Once the application is running, open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to explore the API.

### Run Locally

Create and activate a virtual environment, then install the dependencies:

```bash
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

Install dependencies and start the server:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Make sure PostgreSQL is running and your `.env` file is configured before starting the application.

## 📡 API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/signup` | Register a user |
| POST | `/auth/login` | Log in |
| GET | `/auth/me` | Get current user details |
| POST | `/documents/upload` | Upload a document |
| GET | `/documents/` | List documents |
| DELETE | `/documents/{document_id}` | Delete a document |
| POST | `/chat/sessions` | Create a chat session |
| POST | `/chat/ask` | Ask a question |
| GET | `/chat/sessions/{session_id}/messages` | View chat history |

For the complete API documentation, visit `/docs` after starting the server.

## 🧪 Testing and CI

The project includes automated tests for document processing, text chunking, FAISS and BM25 retrieval, hybrid search, reranking, and the basic API endpoint.

Run the tests:

```bash
python -m pytest -v
```

Run Ruff:

```bash
python -m ruff check app tests
```

The last recorded test run had **16 passing tests**. GitHub Actions is configured to run the code-quality checks and tests automatically on pushes and pull requests.

## 🔮 Future Improvements

- Expand test coverage for authentication, document uploads, and chat endpoints
- Evaluate RAG performance using RAGAS
- Support multi-document conversations
- Add streaming responses and OCR for scanned PDFs
- Introduce Alembic database migrations

## 👤 Author

**Amritha Dileep Kumar**

Built as a portfolio project to explore RAG, hybrid retrieval, LLM integration, and backend development.
