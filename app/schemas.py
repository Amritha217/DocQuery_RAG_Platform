# Defines the format of data - data the users send and response received.

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

# ---------- User Schemas ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)




# ---------- Auth / Token Schemas ----------

class Token(BaseModel):
    access_token: str
    token_type: str


# ---------- Document Schemas ----------

class DocumentResponse(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)



# ---------- Chat Session Schemas ----------

class ChatSessionCreate(BaseModel):
    document_id: int
    title: str | None = "New Chat"


class ChatSessionResponse(BaseModel):
    id: int
    title: str
    document_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



# ---------- Chat Message Schemas ----------

class ChatRequest(BaseModel):
    session_id: int
    question: str


class SourceChunk(BaseModel):
    chunk: str
    page: int | None = None
    score: float

class ChatResponse(BaseModel):
    id: int
    question: str
    answer: str
    sources: list[SourceChunk] | None = None
    session_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
