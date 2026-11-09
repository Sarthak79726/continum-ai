import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.config import settings
from app.core.dependencies import get_current_user, check_project_access
from app.models.all_models import (
    Document, DocumentChunk, Project, User, UserRole, DocumentStatus, AuditLog
)
from app.schemas.all_schemas import DocumentResponse, DocumentChunkResponse
from app.services.document_processor.pipeline import process_document_file
from app.services.vector_store.chroma_service import vector_store

router = APIRouter(tags=["Documents"])

SUPPORTED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "csv", "md"}

@router.post("/projects/{project_id}/documents", response_model=List[DocumentResponse])
async def upload_documents(
    project_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = check_project_access(project_id, current_user, db)

    uploaded_docs = []
    
    for file in files:
        filename = file.filename or "unnamed_file"
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        
        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format for '{filename}'. Allowed formats: PDF, DOCX, TXT, CSV."
            )

        # Create project upload dir
        proj_upload_dir = os.path.join(settings.UPLOAD_DIRECTORY, f"project_{project_id}")
        os.makedirs(proj_upload_dir, exist_ok=True)
        
        saved_path = os.path.join(proj_upload_dir, f"{int(os.times().elapsed*1000)}_{filename}")
        
        # Save file to disk
        size = 0
        with open(saved_path, "wb") as f_out:
            while chunk := await file.read(1024 * 64):
                size += len(chunk)
                if size > settings.MAX_UPLOAD_SIZE:
                    os.remove(saved_path)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"File '{filename}' exceeds maximum allowed size of 20MB."
                    )
                f_out.write(chunk)

        # Create Document in DB
        doc = Document(
            project_id=project.id,
            uploaded_by=current_user.id,
            filename=filename,
            file_type=ext,
            file_size=size,
            storage_path=saved_path,
            processing_status=DocumentStatus.PROCESSING.value
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Execute Document Processing Pipeline (Extract -> Clean -> Chunk)
        try:
            chunks_data = process_document_file(saved_path, ext)
            all_chunks_to_index = []

            for c in chunks_data:
                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    project_id=project.id,
                    chunk_index=c["chunk_index"],
                    page_number=c.get("page_number", 1),
                    section_title=c.get("section_title"),
                    extracted_text=c["text"],
                    token_count=c.get("token_count", 0)
                )
                db.add(db_chunk)
                db.commit()
                db.refresh(db_chunk)

                all_chunks_to_index.append({
                    "id": str(db_chunk.id),
                    "text": db_chunk.extracted_text,
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "page_number": db_chunk.page_number,
                    "chunk_index": db_chunk.chunk_index
                })

            # Store in ChromaDB vector store
            vector_store.add_chunks(project.id, all_chunks_to_index)

            doc.processing_status = DocumentStatus.PROCESSED.value
            db.commit()
        except Exception as e:
            doc.processing_status = DocumentStatus.FAILED.value
            doc.error_message = str(e)
            db.commit()

        uploaded_docs.append(DocumentResponse(
            id=doc.id,
            project_id=doc.project_id,
            uploaded_by=doc.uploaded_by,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            processing_status=doc.processing_status,
            error_message=doc.error_message,
            chunk_count=len(doc.chunks),
            created_at=doc.created_at
        ))

    audit = AuditLog(
        user_id=current_user.id,
        project_id=project.id,
        action="DOCUMENTS_UPLOADED",
        details=f"Uploaded {len(files)} document(s) to project '{project.name}'."
    )
    db.add(audit)
    db.commit()

    return uploaded_docs

@router.get("/projects/{project_id}/documents", response_model=List[DocumentResponse])
def list_project_documents(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = check_project_access(project_id, current_user, db)
    docs = db.query(Document).filter(Document.project_id == project.id).order_by(Document.created_at.desc()).all()

    return [
        DocumentResponse(
            id=d.id,
            project_id=d.project_id,
            uploaded_by=d.uploaded_by,
            filename=d.filename,
            file_type=d.file_type,
            file_size=d.file_size,
            processing_status=d.processing_status,
            error_message=d.error_message,
            chunk_count=len(d.chunks),
            created_at=d.created_at
        )
        for d in docs
    ]

@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    check_project_access(doc.project_id, current_user, db)

    return DocumentResponse(
        id=doc.id,
        project_id=doc.project_id,
        uploaded_by=doc.uploaded_by,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        processing_status=doc.processing_status,
        error_message=doc.error_message,
        chunk_count=len(doc.chunks),
        created_at=doc.created_at
    )

@router.get("/documents/{document_id}/chunks", response_model=List[DocumentChunkResponse])
def get_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    check_project_access(doc.project_id, current_user, db)

    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index).all()
    return chunks

@router.get("/documents/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    check_project_access(doc.project_id, current_user, db)

    if not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document file does not exist on storage.")

    media_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "csv": "text/csv",
        "txt": "text/plain",
        "md": "text/markdown"
    }
    media_type = media_types.get(doc.file_type.lower(), "application/octet-stream")

    return FileResponse(
        path=doc.storage_path,
        filename=doc.filename,
        media_type=media_type
    )

@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    check_project_access(
        doc.project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
    )

    # Delete from ChromaDB
    vector_store.delete_document_chunks(doc.project_id, doc.id)

    # Delete local file if exists
    if os.path.exists(doc.storage_path):
        try:
            os.remove(doc.storage_path)
        except Exception:
            pass

    db.delete(doc)
    db.commit()
    return None

