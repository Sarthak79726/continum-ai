from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user, check_project_access
from app.models.all_models import (
    HandoverReport, Review, Project, User, UserRole, ReportStatus, AuditLog
)
from app.schemas.all_schemas import (
    HandoverCreate, HandoverUpdate, HandoverResponse, ReviewCreate, ReviewResponse
)
from app.services.handover_generator.generator import build_handover_content
from app.services.handover_generator.pdf_exporter import generate_handover_pdf

router = APIRouter(tags=["Handover Reports & Review Centre"])

@router.post("/projects/{project_id}/handovers", response_model=HandoverResponse, status_code=status.HTTP_201_CREATED)
def generate_handover_report(
    project_id: int,
    req: HandoverCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = check_project_access(project_id, current_user, db)

    # Count prior reports to increment version
    prior_count = db.query(HandoverReport).filter(HandoverReport.project_id == project.id).count()
    version = prior_count + 1

    content = build_handover_content(
        db=db,
        project=project,
        view_mode=req.view_mode or "incoming_member_view",
        creator_name=current_user.name
    )

    report_title = req.title or f"Knowledge Handover & Continuity Plan — {project.name} (v{version})"

    report = HandoverReport(
        project_id=project.id,
        created_by=current_user.id,
        title=report_title,
        report_content=content,
        status=ReportStatus.PENDING_REVIEW.value,
        version=version,
        view_mode=req.view_mode or "incoming_member_view"
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    audit = AuditLog(
        user_id=current_user.id,
        project_id=project.id,
        action="HANDOVER_REPORT_GENERATED",
        details=f"Generated Handover Report v{version} for '{project.name}'."
    )
    db.add(audit)
    db.commit()

    return HandoverResponse(
        id=report.id,
        project_id=report.project_id,
        project_name=project.name,
        created_by=report.created_by,
        creator_name=current_user.name,
        title=report.title,
        report_content=report.report_content,
        status=report.status,
        version=report.version,
        view_mode=report.view_mode,
        created_at=report.created_at,
        updated_at=report.updated_at,
        reviews=[]
    )

@router.get("/projects/{project_id}/handovers", response_model=List[HandoverResponse])
def list_project_handovers(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = check_project_access(project_id, current_user, db)
    reports = db.query(HandoverReport).filter(
        HandoverReport.project_id == project.id
    ).order_by(HandoverReport.version.desc()).all()

    result = []
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
        result.append(HandoverResponse(
            id=r.id,
            project_id=r.project_id,
            project_name=project.name,
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
        ))
    return result

@router.get("/handovers/{report_id}", response_model=HandoverResponse)
def get_handover_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(HandoverReport).filter(HandoverReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Handover report not found")

    project = check_project_access(report.project_id, current_user, db)

    reviews_list = [
        ReviewResponse(
            id=rev.id,
            report_id=rev.report_id,
            reviewer_id=rev.reviewer_id,
            reviewer_name=rev.reviewer.name if rev.reviewer else "Unknown",
            action=rev.action,
            comments=rev.comments,
            created_at=rev.created_at
        ) for rev in report.reviews
    ]

    return HandoverResponse(
        id=report.id,
        project_id=report.project_id,
        project_name=project.name,
        created_by=report.created_by,
        creator_name=report.creator.name if report.creator else "Unknown",
        title=report.title,
        report_content=report.report_content,
        status=report.status,
        version=report.version,
        view_mode=report.view_mode,
        created_at=report.created_at,
        updated_at=report.updated_at,
        reviews=reviews_list
    )

@router.put("/handovers/{report_id}", response_model=HandoverResponse)
def update_handover_report(
    report_id: int,
    report_in: HandoverUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(HandoverReport).filter(HandoverReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Handover report not found")

    project = check_project_access(
        report.project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
    )

    if report_in.title is not None:
        report.title = report_in.title
    if report_in.report_content is not None:
        report.report_content = report_in.report_content
    if report_in.status is not None:
        report.status = report_in.status

    db.commit()
    db.refresh(report)

    return HandoverResponse(
        id=report.id,
        project_id=report.project_id,
        project_name=project.name,
        created_by=report.created_by,
        creator_name=report.creator.name if report.creator else "Unknown",
        title=report.title,
        report_content=report.report_content,
        status=report.status,
        version=report.version,
        view_mode=report.view_mode,
        created_at=report.created_at,
        updated_at=report.updated_at,
        reviews=[]
    )

@router.post("/handovers/{report_id}/approve", response_model=HandoverResponse)
def approve_handover_report(
    report_id: int,
    rev_in: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(HandoverReport).filter(HandoverReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Handover report not found")

    project = check_project_access(
        report.project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
    )

    report.status = ReportStatus.APPROVED.value

    review = Review(
        report_id=report.id,
        reviewer_id=current_user.id,
        action="APPROVED",
        comments=rev_in.comments or "Report thoroughly inspected, claims verified against source documents, and approved."
    )
    db.add(review)

    audit = AuditLog(
        user_id=current_user.id,
        project_id=project.id,
        action="HANDOVER_APPROVED",
        details=f"Handover report '{report.title}' marked APPROVED by {current_user.name}."
    )
    db.add(audit)
    db.commit()
    db.refresh(report)

    reviews_list = [
        ReviewResponse(
            id=rev.id,
            report_id=rev.report_id,
            reviewer_id=rev.reviewer_id,
            reviewer_name=rev.reviewer.name if rev.reviewer else "Unknown",
            action=rev.action,
            comments=rev.comments,
            created_at=rev.created_at
        ) for rev in report.reviews
    ]

    return HandoverResponse(
        id=report.id,
        project_id=report.project_id,
        project_name=project.name,
        created_by=report.created_by,
        creator_name=report.creator.name if report.creator else "Unknown",
        title=report.title,
        report_content=report.report_content,
        status=report.status,
        version=report.version,
        view_mode=report.view_mode,
        created_at=report.created_at,
        updated_at=report.updated_at,
        reviews=reviews_list
    )

@router.post("/handovers/{report_id}/reject", response_model=HandoverResponse)
def reject_handover_report(
    report_id: int,
    rev_in: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(HandoverReport).filter(HandoverReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Handover report not found")

    project = check_project_access(
        report.project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
    )

    report.status = ReportStatus.REJECTED.value

    review = Review(
        report_id=report.id,
        reviewer_id=current_user.id,
        action="REJECTED",
        comments=rev_in.comments or "Report returned for revisions. Inconsistencies or missing context identified."
    )
    db.add(review)

    audit = AuditLog(
        user_id=current_user.id,
        project_id=project.id,
        action="HANDOVER_REJECTED",
        details=f"Handover report '{report.title}' REJECTED with comments."
    )
    db.add(audit)
    db.commit()
    db.refresh(report)

    reviews_list = [
        ReviewResponse(
            id=rev.id,
            report_id=rev.report_id,
            reviewer_id=rev.reviewer_id,
            reviewer_name=rev.reviewer.name if rev.reviewer else "Unknown",
            action=rev.action,
            comments=rev.comments,
            created_at=rev.created_at
        ) for rev in report.reviews
    ]

    return HandoverResponse(
        id=report.id,
        project_id=report.project_id,
        project_name=project.name,
        created_by=report.created_by,
        creator_name=report.creator.name if report.creator else "Unknown",
        title=report.title,
        report_content=report.report_content,
        status=report.status,
        version=report.version,
        view_mode=report.view_mode,
        created_at=report.created_at,
        updated_at=report.updated_at,
        reviews=reviews_list
    )

@router.get("/handovers/{report_id}/pdf")
def export_handover_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(HandoverReport).filter(HandoverReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Handover report not found")

    check_project_access(report.project_id, current_user, db)

    pdf_buffer = generate_handover_pdf(report.report_content)
    
    clean_filename = f"Continuum_Handover_{report.project_id}_v{report.version}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={clean_filename}"
        }
    )

