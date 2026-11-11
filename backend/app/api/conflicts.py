from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.all_models import User, ConflictItem
from app.schemas.all_schemas import ConflictItemResponse

router = APIRouter(prefix="/conflicts", tags=["Conflict & Uncertainty Intelligence"])

class ConflictResolveRequest(BaseModel):
    resolution_notes: str

@router.get("/project/{project_id}", response_model=List[ConflictItemResponse])
def list_project_conflicts(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all detected conflicting claims across project artifacts and code repositories."""
    conflicts = db.query(ConflictItem).filter(ConflictItem.project_id == project_id).all()
    return conflicts

@router.post("/{conflict_id}/resolve", response_model=ConflictItemResponse)
def resolve_conflict(
    conflict_id: int,
    req: ConflictResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Allow an authorized reviewer to resolve an artifact conflict with recorded justification."""
    conflict = db.query(ConflictItem).filter(ConflictItem.id == conflict_id).first()
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict record not found")

    conflict.resolution_status = "resolved"
    conflict.resolved_by = current_user.name
    conflict.resolution_notes = req.resolution_notes
    db.commit()
    db.refresh(conflict)
    return conflict

