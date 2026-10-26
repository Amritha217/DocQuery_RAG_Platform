# Define the project database structure

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

# 1. Define the users table, which stores information about registered users

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    documents = relationship("Document", back_populates="owner")
    sessions = relationship("ChatSession", back_populates="user")


# 2. Define documents table, which stores information about each uploaded document.
    
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    storage_key = Column(String, nullable=True, unique=True)                   # This supports vector-store folder arrangement

    owner = relationship("User", back_populates="documents")
    sessions = relationship("ChatSession", back_populates="document")


# 3. Define chat_sessions table, which represents a conversation associated with a user and a document
    
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, default="New Chat")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sessions")
    document = relationship("Document", back_populates="sessions")
    messages = relationship("ChatHistory", back_populates="session", cascade="all, delete-orphan")

# 4. Define the chat_history table, which stores the questions users ask and the answers the chatbot generates
    
class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")