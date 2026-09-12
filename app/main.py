from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth_routes, document_routes, chat_routes

app = FastAPI(
    title="AI-Tutor",
    description="A RAG-based Q&A platform for textbooks",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(document_routes.router)
app.include_router(chat_routes.router)

@app.get("/")
def read_root():
    return {"message": "AI-Tutor API is running!"}