from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.all_models import HandoverReport, Project, User, UserRole
from app.schemas.all_schemas import HandoverResponse, ReviewResponse

router = APIRouter(tags=["Review Centre"])

@router.get("/reviews")
def list_review_center_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    if current_user.role == UserRole.ADMIN.value:
        reports = db.query(HandoverReport).order_by(HandoverReport.updated_at.desc()).all()
    else:
        # Projects user owns or is manager of
        reports = db.query(HandoverReport).join(Project).filter(
            (Project.owner_id == current_user.id)
        ).order_by(HandoverReport.updated_at.desc()).all()

    pending = []
    approved = []
    rejected = []

    for r in reports:
        reviews_list = [
            ReviewResponse(
                id=rev.id,
                report_id=rev.report_id,
                reviewer_id=rev.reviewer_id,
                reviewer_name=rev.reviewer.name if rev.reviewer else "Unknown",
                action=rev.action,
                comments=rev.comments,
                created_at=rev.created_at
            ) for rev in r.reviews
        ]
        item = HandoverResponse(
            id=r.id,
            project_id=r.project_id,
            project_name=r.project.name if r.project else "Project",
            created_by=r.created_by,
            creator_name=r.creator.name if r.creator else "Unknown",
            title=r.title,
            report_content=r.report_content,
            status=r.status,
            version=r.version,
            view_mode=r.view_mode,
            created_at=r.created_at,
            updated_at=r.updated_at,
            reviews=reviews_list
        )
        if r.status == "approved":
            approved.append(item)
        elif r.status == "rejected":
            rejected.append(item)
        else:
            pending.append(item)

    return {
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "total_reviews": len(reports)
    }

