from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user, check_project_access
from app.models.all_models import (
    Project, ProjectMembership, Document, Task, Risk, User, UserRole, AuditLog
)
from app.schemas.all_schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.vector_store.chroma_service import vector_store

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("", response_model=List[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.ADMIN.value:
        projects = db.query(Project).all()
    else:
        # Projects owned or memberships
        member_proj_ids = [
            m.project_id for m in db.query(ProjectMembership).filter(ProjectMembership.user_id == current_user.id).all()
        ]
        projects = db.query(Project).filter(
            (Project.owner_id == current_user.id) | (Project.id.in_(member_proj_ids))
        ).all()

    result = []
    for p in projects:
        doc_count = db.query(Document).filter(Document.project_id == p.id).count()
        task_count = db.query(Task).filter(Task.project_id == p.id).count()
        risk_count = db.query(Risk).filter(Risk.project_id == p.id).count()
        
        resp = ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            status=p.status,
            owner_id=p.owner_id,
            is_demo=p.is_demo,
            created_at=p.created_at,
            updated_at=p.updated_at,
            owner_name=p.owner.name if p.owner else "Unknown",
            document_count=doc_count,
            task_count=task_count,
            risk_count=risk_count
        )
        result.append(resp)
    return result

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = Project(
        name=project_in.name.strip(),
        description=project_in.description.strip() if project_in.description else None,
        status=project_in.status or "active",
        owner_id=current_user.id,
        is_demo=False
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Add owner membership
    membership = ProjectMembership(
        project_id=project.id,
        user_id=current_user.id,
        role=UserRole.PROJECT_MANAGER.value
    )
    db.add(membership)

    audit = AuditLog(
        user_id=current_user.id,
        project_id=project.id,
        action="PROJECT_CREATED",
        details=f"Project '{project.name}' initialized."
    )
    db.add(audit)
    db.commit()

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        owner_id=project.owner_id,
        is_demo=project.is_demo,
        created_at=project.created_at,
        updated_at=project.updated_at,
        owner_name=current_user.name,
        document_count=0,
        task_count=0,
        risk_count=0
    )

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = check_project_access(project_id, current_user, db)
    doc_count = db.query(Document).filter(Document.project_id == project.id).count()
    task_count = db.query(Task).filter(Task.project_id == project.id).count()
    risk_count = db.query(Risk).filter(Risk.project_id == project.id).count()

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        owner_id=project.owner_id,
        is_demo=project.is_demo,
        created_at=project.created_at,
        updated_at=project.updated_at,
        owner_name=project.owner.name if project.owner else "Unknown",
        document_count=doc_count,
        task_count=task_count,
        risk_count=risk_count
    )

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = check_project_access(
        project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
    )

    if project_in.name is not None:
        project.name = project_in.name.strip()
    if project_in.description is not None:
        project.description = project_in.description.strip()
    if project_in.status is not None:
        project.status = project_in.status

    db.commit()
    db.refresh(project)

    doc_count = db.query(Document).filter(Document.project_id == project.id).count()
    task_count = db.query(Task).filter(Task.project_id == project.id).count()
    risk_count = db.query(Risk).filter(Risk.project_id == project.id).count()

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        owner_id=project.owner_id,
        is_demo=project.is_demo,
        created_at=project.created_at,
        updated_at=project.updated_at,
        owner_name=project.owner.name if project.owner else "Unknown",
        document_count=doc_count,
        task_count=task_count,
        risk_count=risk_count
    )

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = check_project_access(
        project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
    )

    # Clean up ChromaDB collection
    vector_store.delete_project_collection(project.id)

    # Clean up audit logs
    db.query(AuditLog).filter(AuditLog.project_id == project.id).delete()

    db.delete(project)
    db.commit()
    return None

@router.get("/{project_id}/audit-logs")
def get_project_audit_logs(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = check_project_access(project_id, current_user, db)
    logs = db.query(AuditLog).filter(
        AuditLog.project_id == project.id
    ).order_by(AuditLog.created_at.desc()).all()

    return [{
        "id": log.id,
        "action": log.action,
        "details": log.details,
        "user_id": log.user_id,
        "user_name": log.user.name if log.user else "System",
        "created_at": log.created_at
    } for log in logs]

