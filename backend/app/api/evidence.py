from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user, check_project_access
from app.models.all_models import Evidence, Document, User, UserRole, AuditLog
from app.schemas.all_schemas import EvidenceResponse, EvidenceVerifyRequest

router = APIRouter(tags=["Evidence Passport"])

@router.get("/projects/{project_id}/evidence", response_model=List[EvidenceResponse])
def get_project_evidence(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = check_project_access(project_id, current_user, db)

    items = db.query(Evidence).filter(
        Evidence.project_id == project.id
    ).order_by(Evidence.id.desc()).all()

    results = []
    for ev in items:
        doc = db.query(Document).filter(Document.id == ev.document_id).first()
        results.append(EvidenceResponse(
            id=ev.id,
            project_id=ev.project_id,
            document_id=ev.document_id,
            document_name=doc.filename if doc else "Document",
            chunk_id=ev.chunk_id,
            claim_text=ev.claim_text,
            source_snippet=ev.source_snippet,
            page_number=ev.page_number,
            verification_status=ev.verification_status,
            quality_label=ev.quality_label,
            created_at=ev.created_at
        ))
    return results

@router.put("/evidence/{evidence_id}", response_model=EvidenceResponse)
def update_evidence_status(
    evidence_id: int,
    req: EvidenceVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ev = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence record not found")

    project = check_project_access(
        ev.project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
    )

    ev.verification_status = req.verification_status
    if req.quality_label:
        ev.quality_label = req.quality_label

    audit = AuditLog(
        user_id=current_user.id,
        project_id=ev.project_id,
        action="EVIDENCE_VERIFIED",
        details=f"Updated evidence {ev.id} claim status to '{req.verification_status}'."
    )
    db.add(audit)
    db.commit()
    db.refresh(ev)

    doc = db.query(Document).filter(Document.id == ev.document_id).first()
    return EvidenceResponse(
        id=ev.id,
        project_id=ev.project_id,
        document_id=ev.document_id,
        document_name=doc.filename if doc else "Document",
        chunk_id=ev.chunk_id,
        claim_text=ev.claim_text,
        source_snippet=ev.source_snippet,
        page_number=ev.page_number,
        verification_status=ev.verification_status,
        quality_label=ev.quality_label,
        created_at=ev.created_at
    )

