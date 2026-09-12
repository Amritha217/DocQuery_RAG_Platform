from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# ---------- User Schemas ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Auth / Token Schemas ----------

class Token(BaseModel):
    access_token: str
    token_type: str


# ---------- Document Schemas ----------

class DocumentResponse(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ---------- Chat Session Schemas ----------

class ChatSessionCreate(BaseModel):
    document_id: int
    title: Optional[str] = "New Chat"


class ChatSessionResponse(BaseModel):
    id: int
    title: str
    document_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Chat Message Schemas ----------

class ChatRequest(BaseModel):
    session_id: int
    question: str


class SourceChunk(BaseModel):
    chunk: str
    page: Optional[int] = None
    score: float

class ChatResponse(BaseModel):
    id: int
    question: str
    answer: str
    sources: Optional[list[SourceChunk]] = None
    session_id: int
    created_at: datetime

    class Config:
        from_attributes = True