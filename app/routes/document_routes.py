# Manages documents for chatbot - uploading , listing and deleting document

import os
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.services.document_processing import chunk_pages, extract_pages
from app.services.retrieval_service import (
    create_bm25_index,
    create_faiss_index,
    create_storage_key,
    delete_document_index,
)

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = (".pdf", ".docx", ".txt")


# Upload and process a document
@router.post("/upload", response_model=schemas.DocumentResponse)

# 1. Uploading document

# - Checks whether the uploaded file is a PDF, DOCX, or TXT file
# - Creates a folder for the logged-in user
# - Saves the uploaded file to that folder
# - Saves the document's information in the database
# - Extracts text from the document
# - Splits the extracted text into smaller chunks
# - Creates a FAISS vector index and a BM25 keyword-search index
# - Handles errors by attempting to remove the uploaded file and database record if processing fails
# - Returns the saved document information


@router.post("/upload", response_model=schemas.DocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filename = os.path.basename(file.filename or "")

    if not filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX, and TXT files are allowed.",
        )

    user_folder = os.path.join(UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_folder, exist_ok=True)

    file_path = os.path.join(user_folder, filename)
    storage_key = None
    document = None

    try:
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Assign a folder such as Biology/1
        storage_key = create_storage_key(filename)

        # Save document information in the database
        document = models.Document(
            filename=filename,
            filepath=file_path,
            owner_id=current_user.id,
            storage_key=storage_key,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        # Extract text and split it into chunks
        pages = extract_pages(file_path)
        chunks = chunk_pages(pages)

        if not chunks:
            raise ValueError("No readable text was found in the document.")

        # Create search indexes inside the assigned folder
        create_faiss_index(storage_key, chunks)
        create_bm25_index(storage_key, chunks)

        return document

    except Exception as error:
        db.rollback()

        # Remove any index files created for this upload
        if storage_key:
            delete_document_index(storage_key)

        # Remove the uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)

        # Remove the database record if it was saved
        if document is not None and document.id is not None:
            db.delete(document)
            db.commit()

        if isinstance(error, HTTPException):
            raise

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload or process document.",
        ) from error



# List the current user's documents
@router.get("/", response_model=list[schemas.DocumentResponse])

# 2. Retrieve all documents belonging to the logged-in user

# - Identifies the currently logged-in user
# - Searches the database for documents owned by that user
# - Retrieves all matching documents
# - Returns the documents using the DocumentResponse schema

def list_documents(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Document)
        .filter(models.Document.owner_id == current_user.id)
        .all()
    )


# Delete a document
@router.delete("/{document_id}")

# 3. Delete a document belonging to the logged-in user

# - Searches for the document using its ID and the logged-in user's ID
# - Checks whether the document exists and belongs to that user
# - Returns a 404 error if the document is not found or does not belong to the user
# - Deletes the uploaded file from storage if it exists
# - Deletes the document record from the database
# - Returns a success message


def delete_document(
    document_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    #  Find the document owned by the current user
    document = (
        db.query(models.Document)
        .filter(
            models.Document.id == document_id,
            models.Document.owner_id == current_user.id,
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    try:
        #  Delete the vector-store folder and its index files
        if document.storage_key:
            delete_document_index(document.storage_key)

        #  Delete the uploaded file
        if os.path.exists(document.filepath):
            os.remove(document.filepath)

        # Delete the document record from the database
        db.delete(document)
        db.commit()

        return {"message": "Document deleted successfully"}

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        ) from error
