from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user, check_project_access
from app.models.all_models import Task, User, UserRole, AuditLog
from app.schemas.all_schemas import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(tags=["Tasks & Continuity Blueprint"])

@router.get("/projects/{project_id}/tasks", response_model=List[TaskResponse])
def list_project_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = check_project_access(project_id, current_user, db)
    tasks = db.query(Task).filter(Task.project_id == project.id).order_by(Task.is_recommendation.desc(), Task.id.asc()).all()
    return tasks

@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    project_id: int,
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = check_project_access(
        project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.TEAM_MEMBER.value]
    )

    task = Task(
        project_id=project.id,
        title=task_in.title.strip(),
        description=task_in.description.strip() if task_in.description else None,
        status=task_in.status or "pending",
        priority=task_in.priority or "medium",
        owner=task_in.owner or "Unassigned",
        due_date=task_in.due_date,
        source_reference=task_in.source_reference or "Manual Entry",
        is_recommendation=task_in.is_recommendation or False
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return task

@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    check_project_access(
        task.project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.TEAM_MEMBER.value]
    )

    if task_in.title is not None:
        task.title = task_in.title.strip()
    if task_in.description is not None:
        task.description = task_in.description.strip()
    if task_in.status is not None:
        task.status = task_in.status
    if task_in.priority is not None:
        task.priority = task_in.priority
    if task_in.owner is not None:
        task.owner = task_in.owner
    if task_in.due_date is not None:
        task.due_date = task_in.due_date
    if task_in.is_recommendation is not None:
        task.is_recommendation = task_in.is_recommendation

    db.commit()
    db.refresh(task)
    return task

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    check_project_access(
        task.project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.TEAM_MEMBER.value]
    )
    db.delete(task)
    db.commit()
    return None

