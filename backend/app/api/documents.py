import os
import re
import uuid
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

def validate_file_signature(ext: str, header: bytes) -> bool:
    """Validate file magic bytes / signature against declared extension."""
    if ext == "pdf":
        return header.startswith(b"%PDF-")
    elif ext in ("docx", "doc"):
        return header.startswith(b"PK\x03\x04") or header.startswith(b"\xd0\xcf\x11\xe0")
    elif ext in ("csv", "txt", "md"):
        if b"\x00" in header:
            return False
        try:
            header.decode("utf-8")
            return True
        except UnicodeDecodeError:
            try:
                header.decode("latin-1")
                return True
            except UnicodeDecodeError:
                return False
    return False

@router.post("/projects/{project_id}/documents", response_model=List[DocumentResponse])
async def upload_documents(
    project_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = check_project_access(
        project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.TEAM_MEMBER.value]
    )

    uploaded_docs = []
    
    for file in files:
        raw_name = file.filename or "unnamed_file"
        clean_basename = os.path.basename(raw_name)
        safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', clean_basename)
        ext = safe_name.split(".")[-1].lower() if "." in safe_name else ""
        
        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format for '{safe_name}'. Allowed formats: PDF, DOCX, TXT, CSV, MD."
            )

        # Create project upload dir with path verification
        proj_upload_dir = os.path.join(settings.UPLOAD_DIRECTORY, f"project_{project_id}")
        os.makedirs(proj_upload_dir, exist_ok=True)
        canonical_dir = os.path.abspath(proj_upload_dir)

        disk_filename = f"{uuid.uuid4().hex}_{safe_name}"
        saved_path = os.path.join(proj_upload_dir, disk_filename)
        if not os.path.abspath(saved_path).startswith(canonical_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path."
            )

        # Validate header magic bytes
        first_chunk = await file.read(1024)
        if not first_chunk:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Uploaded file '{safe_name}' is empty."
            )

        if not validate_file_signature(ext, first_chunk):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File signature does not match declared extension for '{safe_name}'."
            )
        
        # Save file to disk safely
        size = len(first_chunk)
        if size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{safe_name}' exceeds maximum allowed size of 20MB."
            )

        try:
            with open(saved_path, "wb") as f_out:
                f_out.write(first_chunk)
                while chunk := await file.read(1024 * 64):
                    size += len(chunk)
                    if size > settings.MAX_UPLOAD_SIZE:
                        f_out.close()
                        if os.path.exists(saved_path):
                            os.remove(saved_path)
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"File '{safe_name}' exceeds maximum allowed size of 20MB."
                        )
                    f_out.write(chunk)
        except HTTPException:
            raise
        except Exception as e:
            if os.path.exists(saved_path):
                os.remove(saved_path)
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

        # Create Document in DB
        doc = Document(
            project_id=project.id,
            uploaded_by=current_user.id,
            filename=safe_name,
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

    canonical_upload_root = os.path.abspath(settings.UPLOAD_DIRECTORY)
    canonical_file_path = os.path.abspath(doc.storage_path)
    if not canonical_file_path.startswith(canonical_upload_root):
        raise HTTPException(status_code=403, detail="Access to file path is forbidden.")

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

    # Delete local file if exists within canonical upload root
    canonical_upload_root = os.path.abspath(settings.UPLOAD_DIRECTORY)
    canonical_file_path = os.path.abspath(doc.storage_path)
    if canonical_file_path.startswith(canonical_upload_root) and os.path.exists(doc.storage_path):
        try:
            os.remove(doc.storage_path)
        except Exception:
            pass

    db.delete(doc)
    db.commit()
    return None

