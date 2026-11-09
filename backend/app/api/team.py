from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user, check_project_access
from app.models.all_models import (
    Project, ProjectMembership, User, UserRole, AuditLog
)
from app.schemas.all_schemas import ProjectMemberAdd, ProjectMemberResponse

router = APIRouter(tags=["Team & Access Management"])

@router.get("/projects/{project_id}/members", response_model=List[ProjectMemberResponse])
def get_project_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = check_project_access(project_id, current_user, db)

    memberships = db.query(ProjectMembership).filter(
        ProjectMembership.project_id == project.id
    ).all()

    result = []
    # Include owner first
    if project.owner:
        result.append(ProjectMemberResponse(
            id=0,
            user_id=project.owner.id,
            project_id=project.id,
            name=f"{project.owner.name} (Project Owner)",
            email=project.owner.email,
            role="PROJECT_MANAGER",
            created_at=project.created_at
        ))

    for m in memberships:
        if m.user_id != project.owner_id and m.user:
            result.append(ProjectMemberResponse(
                id=m.id,
                user_id=m.user_id,
                project_id=m.project_id,
                name=m.user.name,
                email=m.user.email,
                role=m.role,
                created_at=m.created_at
            ))

    return result

@router.post("/projects/{project_id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
def add_project_member(
    project_id: int,
    member_in: ProjectMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = check_project_access(
        project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
    )

    user = db.query(User).filter(User.email == member_in.email.strip().lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"No user found with email '{member_in.email}'")

    existing = db.query(ProjectMembership).filter(
        ProjectMembership.project_id == project.id,
        ProjectMembership.user_id == user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this project")

    membership = ProjectMembership(
        project_id=project.id,
        user_id=user.id,
        role=member_in.role.upper()
    )
    db.add(membership)

    audit = AuditLog(
        user_id=current_user.id,
        project_id=project.id,
        action="MEMBER_ADDED",
        details=f"Added '{user.name}' ({user.email}) as {member_in.role} to '{project.name}'."
    )
    db.add(audit)
    db.commit()
    db.refresh(membership)

    return ProjectMemberResponse(
        id=membership.id,
        user_id=membership.user_id,
        project_id=membership.project_id,
        name=user.name,
        email=user.email,
        role=membership.role,
        created_at=membership.created_at
    )

@router.delete("/projects/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = check_project_access(
        project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
    )

    if user_id == project.owner_id:
        raise HTTPException(status_code=400, detail="Cannot remove project owner from membership.")

    membership = db.query(ProjectMembership).filter(
        ProjectMembership.project_id == project.id,
        ProjectMembership.user_id == user_id
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership record not found")

    db.delete(membership)
    db.commit()
    return None

