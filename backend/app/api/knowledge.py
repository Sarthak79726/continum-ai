from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user, check_project_access
from app.models.all_models import ExtractedKnowledge, User

router = APIRouter(tags=["Knowledge"])

@router.get("/projects/{project_id}/knowledge")
def get_project_knowledge(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    project = check_project_access(project_id, current_user, db)

    entries = db.query(ExtractedKnowledge).filter(
        ExtractedKnowledge.project_id == project.id
    ).all()

    knowledge_map = {}
    for e in entries:
        knowledge_map[e.category] = {
            "id": e.id,
            "category": e.category,
            "content": e.structured_content,
            "verification_status": e.verification_status,
            "created_at": e.created_at
        }

    return {
        "project_id": project.id,
        "project_name": project.name,
        "categories": knowledge_map
    }

