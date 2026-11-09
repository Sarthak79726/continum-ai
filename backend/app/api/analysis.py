from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database.session import get_db
from app.core.dependencies import get_current_user, check_project_access
from app.models.all_models import Project, User, Document, DocumentStatus
from app.services.knowledge_extractor.extractor import KnowledgeExtractor

router = APIRouter(tags=["AI Reconstruction"])

@router.post("/projects/{project_id}/analyse")
def trigger_project_reconstruction(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Core AI Reconstruction Endpoint:
    Processes all indexed project documents, extracts tasks, decisions, risks,
    dependencies, unresolved questions, links source evidence, and updates project knowledge.
    """
    project = check_project_access(project_id, current_user, db)

    # Check if project has any documents
    docs = db.query(Document).filter(
        Document.project_id == project_id,
        Document.processing_status == DocumentStatus.PROCESSED.value
    ).all()

    if not docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot analyze project: No processed documents available. Please upload project documents first."
        )

    extractor = KnowledgeExtractor(db, project)
    analysis_result = extractor.run_reconstruction(current_user.id)

    return {
        "status": "success",
        "message": f"Successfully reconstructed knowledge state for '{project.name}'",
        "analysis": analysis_result
    }

