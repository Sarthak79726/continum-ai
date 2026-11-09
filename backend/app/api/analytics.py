from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.all_models import (
    Project, Document, Task, Risk, HandoverReport, AuditLog, User, UserRole, ProjectMembership
)
from app.schemas.all_schemas import DashboardStats

router = APIRouter(tags=["Analytics & Dashboard"])

@router.get("/analytics", response_model=DashboardStats)
def get_dashboard_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.ADMIN.value:
        projects = db.query(Project).all()
        proj_ids = [p.id for p in projects]
    else:
        member_proj_ids = [
            m.project_id for m in db.query(ProjectMembership).filter(ProjectMembership.user_id == current_user.id).all()
        ]
        projects = db.query(Project).filter(
            (Project.owner_id == current_user.id) | (Project.id.in_(member_proj_ids))
        ).all()
        proj_ids = [p.id for p in projects]

    if not proj_ids:
        return DashboardStats(
            total_projects=0,
            documents_processed=0,
            completed_tasks=0,
            pending_tasks=0,
            in_progress_tasks=0,
            identified_risks=0,
            handover_reports=0,
            pending_reviews=0,
            recent_projects=[],
            recent_documents=[],
            pending_review_reports=[],
            activity_timeline=[],
            task_completion_distribution=[
                {"name": "Completed", "value": 0, "color": "#10b981"},
                {"name": "In Progress", "value": 0, "color": "#06b6d4"},
                {"name": "Pending", "value": 0, "color": "#f59e0b"}
            ],
            risk_severity_distribution=[
                {"severity": "Critical", "count": 0},
                {"severity": "High", "count": 0},
                {"severity": "Medium", "count": 0},
                {"severity": "Low", "count": 0}
            ]
        )

    # Aggregates
    total_docs = db.query(Document).filter(
        Document.project_id.in_(proj_ids),
        Document.processing_status == "processed"
    ).count()

    tasks = db.query(Task).filter(Task.project_id.in_(proj_ids)).all()
    completed_tasks = len([t for t in tasks if t.status == "completed"])
    in_prog_tasks = len([t for t in tasks if t.status == "in_progress"])
    pending_tasks = len([t for t in tasks if t.status in ["pending", "blocked"]])

    risks = db.query(Risk).filter(Risk.project_id.in_(proj_ids)).all()
    total_risks = len(risks)

    reports = db.query(HandoverReport).filter(HandoverReport.project_id.in_(proj_ids)).all()
    total_reports = len(reports)
    pending_revs = len([r for r in reports if r.status == "pending_review"])

    # Recent projects
    recent_projects_data = [{
        "id": p.id,
        "name": p.name,
        "status": p.status,
        "is_demo": p.is_demo,
        "created_at": p.created_at.strftime("%Y-%m-%d"),
        "doc_count": len(p.documents),
        "task_count": len(p.tasks)
    } for p in sorted(projects, key=lambda x: x.created_at, reverse=True)[:5]]

    # Recent documents
    docs = db.query(Document).filter(Document.project_id.in_(proj_ids)).order_by(Document.created_at.desc()).limit(5).all()
    recent_docs_data = [{
        "id": d.id,
        "filename": d.filename,
        "file_type": d.file_type.upper(),
        "status": d.processing_status,
        "project_name": d.project.name if d.project else "Project",
        "created_at": d.created_at.strftime("%Y-%m-%d %H:%M")
    } for d in docs]

    # Pending reviews
    pending_reports = [r for r in reports if r.status == "pending_review"][:5]
    pending_revs_data = [{
        "id": r.id,
        "title": r.title,
        "project_name": r.project.name if r.project else "Project",
        "created_by": r.creator.name if r.creator else "Unknown",
        "created_at": r.created_at.strftime("%Y-%m-%d")
    } for r in pending_reports]

    # Activity Timeline from AuditLogs
    audits = db.query(AuditLog).filter(
        (AuditLog.project_id.in_(proj_ids)) | (AuditLog.user_id == current_user.id)
    ).order_by(AuditLog.created_at.desc()).limit(8).all()

    timeline_data = [{
        "id": a.id,
        "action": a.action.replace("_", " ").title(),
        "details": a.details,
        "created_at": a.created_at.strftime("%b %d, %H:%M")
    } for a in audits]

    # Risk Distribution
    crit_count = len([r for r in risks if r.severity.lower() == "critical"])
    high_count = len([r for r in risks if r.severity.lower() == "high"])
    med_count = len([r for r in risks if r.severity.lower() == "medium"])
    low_count = len([r for r in risks if r.severity.lower() == "low"])

    return DashboardStats(
        total_projects=len(projects),
        documents_processed=total_docs,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        in_progress_tasks=in_prog_tasks,
        identified_risks=total_risks,
        handover_reports=total_reports,
        pending_reviews=pending_revs,
        recent_projects=recent_projects_data,
        recent_documents=recent_docs_data,
        pending_review_reports=pending_revs_data,
        activity_timeline=timeline_data,
        task_completion_distribution=[
            {"name": "Completed", "value": completed_tasks, "color": "#10b981"},
            {"name": "In Progress", "value": in_prog_tasks, "color": "#06b6d4"},
            {"name": "Pending", "value": pending_tasks, "color": "#f59e0b"}
        ],
        risk_severity_distribution=[
            {"severity": "Critical", "count": crit_count},
            {"severity": "High", "count": high_count},
            {"severity": "Medium", "count": med_count},
            {"severity": "Low", "count": low_count}
        ]
    )

