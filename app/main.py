# Coonects backend parts so the frontend can communicate with it using API

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth_routes, chat_routes, document_routes

# 1. Creates the FastAPI application

app = FastAPI(
    title="AI-Tutor",
    description="A RAG-based Q&A platform for textbooks",
    version="1.0.0"
)


# 2. Configures CORS so a frontend can communicate with the backend

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Registers the routers - authentication, document, and chat routers

app.include_router(auth_routes.router)
app.include_router(document_routes.router)
app.include_router(chat_routes.router)

# 4. Creates a root endpoint to check that the API is running

@app.get("/")
def read_root():
    return {"message": "AI-Tutor API is running!"}