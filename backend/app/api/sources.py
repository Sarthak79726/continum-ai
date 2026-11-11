from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.session import get_db
from app.core.dependencies import get_current_user, check_project_access
from app.models.all_models import User, UserRole, SourceConnection, EmployeeProfile
from app.schemas.all_schemas import SourceConnectionResponse
from app.services.sources.github_service import github_service

router = APIRouter(prefix="/sources", tags=["Source Integrations"])

class GitHubConnectRequest(BaseModel):
    owner: str
    repo: str
    branch: Optional[str] = "main"
    token: Optional[str] = None

@router.get("/project/{project_id}", response_model=List[SourceConnectionResponse])
def list_project_sources(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all connected sources for a project (GitHub, Docs, Jira, Slack)."""
    check_project_access(project_id, current_user, db)
    sources = db.query(SourceConnection).filter(SourceConnection.project_id == project_id).all()
    return sources

@router.post("/project/{project_id}/github/connect")
async def connect_github_repository(
    project_id: int,
    req: GitHubConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Connect a GitHub repository and synchronize initial commit history."""
    check_project_access(
        project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
    )
    # Find employees in project to attribute commits
    employees = db.query(EmployeeProfile).filter(EmployeeProfile.project_id == project_id).all()
    mapping = {e.name: e.id for e in employees}

    service = github_service
    if req.token:
        from app.services.sources.github_service import GitHubService
        service = GitHubService(token=req.token)

    result = service.sync_repository_to_db(
        project_id=project_id,
        owner=req.owner,
        repo=req.repo,
        db=db,
        employee_mapping=mapping
    )
    return result

@router.post("/project/{project_id}/github/sync")
def sync_github_source(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger incremental sync for connected GitHub repository."""
    check_project_access(
        project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
    )
    conn = db.query(SourceConnection).filter(
        SourceConnection.project_id == project_id,
        SourceConnection.source_type == "github"
    ).first()

    owner = "continuum-campus"
    repo = "smart-campus-core"
    if conn and conn.metadata_json:
        owner = conn.metadata_json.get("owner", owner)
        repo = conn.metadata_json.get("repo", repo)

    employees = db.query(EmployeeProfile).filter(EmployeeProfile.project_id == project_id).all()
    mapping = {e.name: e.id for e in employees}

    result = github_service.sync_repository_to_db(
        project_id=project_id,
        owner=owner,
        repo=repo,
        db=db,
        employee_mapping=mapping
    )
    return result

