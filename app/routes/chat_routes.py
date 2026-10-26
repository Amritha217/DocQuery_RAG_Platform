# handles the chat functionality of your RAG chatbot

# lets users create chat sessions for their uploaded documents, ask questions, retrieve relevant chunks, generate answers using the LLM, and view previous messages.

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.services.llm_service import generate_answer
from app.services.retrieval_service import hybrid_search, rerank_results

router = APIRouter(prefix="/chat", tags=["Chat"])

# Create a chat session for a document

@router.post("/sessions", response_model=schemas.ChatSessionResponse)



# 1. Start a new conversation about a document.

# - Checks whether the document exists and belongs to the logged-in user
# - Creates a new chat session and links it to that user and document
# - Saves the session in the database and returns it

def create_chat_session(
    session_data: schemas.ChatSessionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.query(models.Document).filter(
        models.Document.id == session_data.document_id,
        models.Document.owner_id == current_user.id,
    ).first()

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    new_session = models.ChatSession(
        title=session_data.title,
        user_id=current_user.id,
        document_id=session_data.document_id,
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session


# List sessions for a document

@router.get("/sessions/{document_id}", response_model=list[schemas.ChatSessionResponse])

# 2. Show the user's conversations for a particular document

# - finds all chat sessions associated with the specified document and the logged-in user
# - sorts them from newest to oldest

def list_chat_sessions(
    document_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = db.query(models.ChatSession).filter(
        models.ChatSession.document_id == document_id,
        models.ChatSession.user_id == current_user.id,
    ).order_by(models.ChatSession.created_at.desc()).all()

    return sessions





# Ask a question and generate an answer

@router.post("/ask", response_model=schemas.ChatResponse)


# 3. main RAG function

# takes the user's question and returns an answer based on the document's retrieved content.

# - Checks chat session exists and belongs to the logged-in user. Gets the associated document ID.
# - Calls hybrid_search() - to combine FAISS and BM25 retrieval methods. And gets back 10 chunks using hybrid search
#  - Rerank the retrieved chunks to get the top 5 relevant chunks using rerank_results()
# -  Generate answer by calling generate_answer() with user qns and selected chunks
# - Save chat history - save qns , generated ans , message ID , session ID , creation time to frontend
# - Return response - answer questopn , message ID , session ID , creation time


def ask_question(
    chat_request: schemas.ChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Find the chat session
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == chat_request.session_id,
        models.ChatSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Chat session not found",
        )

    # Find the document belonging to the current user
    document = db.query(models.Document).filter(
        models.Document.id == session.document_id,
        models.Document.owner_id == current_user.id,
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    #  Search using the document's storage_key
    hybrid_results = hybrid_search(
        document.storage_key,
        chat_request.question,
        top_k=10,
    )

    if not hybrid_results:
        answer_text = (
            "I don't have enough information in this document to answer that question."
        )
    else:
        final_chunks = rerank_results(
            chat_request.question,
            hybrid_results,
            top_k=5,
        )
        answer_text = generate_answer(
            chat_request.question,
            final_chunks,
        )

    new_message = models.ChatHistory(
        question=chat_request.question,
        answer=answer_text,
        sources=None,
        session_id=session.id,
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    response = schemas.ChatResponse(
        id=new_message.id,
        question=new_message.question,
        answer=new_message.answer,
        sources=None,
        session_id=new_message.session_id,
        created_at=new_message.created_at,
    )

    return response


# Retrieve previous messages

@router.get("/sessions/{session_id}/messages", response_model=list[schemas.ChatResponse])

# 4. Load a conversation's previous messages.

# - Checks that the chat session belongs to the logged-in user
# - Retrieves all messages for that session
# - Orders them from oldest to newest
# - Converts the saved source JSON back into Python data
# - Returns the messages using the ChatResponse schema

def get_chat_messages(
    session_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id,
        models.ChatSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

    messages = db.query(models.ChatHistory).filter(
        models.ChatHistory.session_id == session_id,
    ).order_by(models.ChatHistory.created_at.asc()).all()

    result = []
    for m in messages:
        result.append(schemas.ChatResponse(
            id=m.id,
            question=m.question,
            answer=m.answer,
            sources=json.loads(m.sources) if m.sources else None,
            session_id=m.session_id,
            created_at=m.created_at,
        ))

    return result