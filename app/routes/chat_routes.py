from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.services.retrieval_service import hybrid_search, rerank_results
from app.services.llm_service import generate_answer

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/sessions", response_model=schemas.ChatSessionResponse)
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


@router.get("/sessions/{document_id}", response_model=list[schemas.ChatSessionResponse])
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


import json

@router.post("/ask", response_model=schemas.ChatResponse)
def ask_question(
    chat_request: schemas.ChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == chat_request.session_id,
        models.ChatSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

    document_id = session.document_id

    hybrid_results = hybrid_search(document_id, chat_request.question, top_k=10)

    if not hybrid_results:
        answer_text = "I don't have enough information in this document to answer that question."
        sources_json = None
    else:
        final_chunks = rerank_results(chat_request.question, hybrid_results, top_k=5)
        answer_text = generate_answer(chat_request.question, final_chunks)

        sources_list = [
            {"chunk": c["chunk"], "page": c.get("page"), "score": c["rerank_score"]} for c in final_chunks
        ]
        sources_json = json.dumps(sources_list)

    new_message = models.ChatHistory(
        question=chat_request.question,
        answer=answer_text,
        sources=sources_json,
        session_id=session.id,
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    response = schemas.ChatResponse(
        id=new_message.id,
        question=new_message.question,
        answer=new_message.answer,
        sources=json.loads(new_message.sources) if new_message.sources else None,
        session_id=new_message.session_id,
        created_at=new_message.created_at,
    )

    return response


@router.get("/sessions/{session_id}/messages", response_model=list[schemas.ChatResponse])
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