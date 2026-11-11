from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user, check_project_access
from app.models.all_models import (
    User, UserRole, EmployeeProfile, ContinuationActionItem,
    HandoverLifecycleStatus
)
from app.schemas.all_schemas import (
    EmployeeProfileCreate, EmployeeProfileUpdate, EmployeeProfileResponse,
    EmployeePassportResponse, ContinuationActionItemResponse,
    HandoverInitiateRequest, HandoverAcknowledgeRequest
)
from app.services.employee_passport.passport_service import passport_service

router = APIRouter(prefix="/employees", tags=["Employees & Knowledge Passports"])

@router.get("/project/{project_id}", response_model=List[EmployeeProfileResponse])
def list_project_employees(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all employees associated with a project."""
    check_project_access(project_id, current_user, db)
    employees = db.query(EmployeeProfile).filter(EmployeeProfile.project_id == project_id).all()
    results = []
    for emp in employees:
        succ_name = None
        if emp.assigned_successor_id:
            succ = db.query(EmployeeProfile).filter(EmployeeProfile.id == emp.assigned_successor_id).first()
            if succ:
                succ_name = succ.name
        res = EmployeeProfileResponse.model_validate(emp)
        res.successor_name = succ_name
        results.append(res)
    return results

@router.post("/project/{project_id}", response_model=EmployeeProfileResponse)
def create_employee_profile(
    project_id: int,
    emp_in: EmployeeProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new employee profile under a project."""
    check_project_access(
        project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
    )
    emp = EmployeeProfile(
        project_id=project_id,
        user_id=emp_in.user_id,
        name=emp_in.name,
        employee_id_code=emp_in.employee_id_code,
        role_title=emp_in.role_title,
        department=emp_in.department or "Engineering",
        responsibilities=emp_in.responsibilities or [],
        date_joined=emp_in.date_joined,
        handover_status=emp_in.handover_status or HandoverLifecycleStatus.ACTIVE.value,
        contribution_summary=emp_in.contribution_summary
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return EmployeeProfileResponse.model_validate(emp)

@router.get("/{employee_id}", response_model=EmployeeProfileResponse)
def get_employee_profile(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve an employee profile."""
    emp = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    check_project_access(emp.project_id, current_user, db)

    succ_name = None
    if emp.assigned_successor_id:
        succ = db.query(EmployeeProfile).filter(EmployeeProfile.id == emp.assigned_successor_id).first()
        if succ:
            succ_name = succ.name
    res = EmployeeProfileResponse.model_validate(emp)
    res.successor_name = succ_name
    return res

@router.put("/{employee_id}", response_model=EmployeeProfileResponse)
def update_employee_profile(
    employee_id: int,
    emp_update: EmployeeProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update employee metadata, role, or successor."""
    emp = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    check_project_access(
        emp.project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
    )

    for field, val in emp_update.model_dump(exclude_unset=True).items():
        setattr(emp, field, val)

    db.commit()
    db.refresh(emp)
    return EmployeeProfileResponse.model_validate(emp)

@router.get("/{employee_id}/passport", response_model=EmployeePassportResponse)
def get_employee_passport(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve the complete technical Employee Knowledge Passport, compiling work timeline,
    commits, PRs, API inventory, database schema, bugs & technical debt, blockers,
    and continuation action items.
    """
    emp = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    check_project_access(emp.project_id, current_user, db)

    try:
        data = passport_service.get_full_passport(employee_id, db)
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{employee_id}/reconstruct", response_model=EmployeePassportResponse)
def reconstruct_employee_knowledge(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger end-to-end knowledge reconstruction for an employee, analyzing
    authorized project evidence, code changes, and task history.
    """
    emp = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    check_project_access(
        emp.project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.TEAM_MEMBER.value]
    )

    try:
        data = passport_service.reconstruct_employee_knowledge(employee_id, db)
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{employee_id}/handover/initiate")
def initiate_employee_handover(
    employee_id: int,
    req: HandoverInitiateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initiate handover process for a departing employee to a designated successor."""
    emp = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    check_project_access(
        emp.project_id, current_user, db,
        allowed_roles=[UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
    )

    data = passport_service.initiate_handover(
        project_id=emp.project_id,
        departing_id=employee_id,
        successor_id=req.successor_id,
        notes=req.notes,
        db=db
    )
    return {"status": "success", "message": "Handover initiated and knowledge reconstructed", "data": data}

@router.post("/{employee_id}/handover/acknowledge")
def acknowledge_employee_handover(
    employee_id: int,
    req: HandoverAcknowledgeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Acknowledge receipt of handover by the incoming successor."""
    emp = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    check_project_access(emp.project_id, current_user, db)

    try:
        res = passport_service.acknowledge_handover(employee_id, req.comments, db)
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{employee_id}/actions", response_model=List[ContinuationActionItemResponse])
def get_employee_continuation_actions(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve continuation action items for an employee transition."""
    emp = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    check_project_access(emp.project_id, current_user, db)

    actions = db.query(ContinuationActionItem).filter(
        ContinuationActionItem.departing_employee_id == employee_id
    ).all()
    return actions

@router.put("/actions/{action_id}/toggle", response_model=ContinuationActionItemResponse)
def toggle_continuation_action(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle completion status of an incoming developer continuation checklist item."""
    from datetime import datetime, timezone
    act = db.query(ContinuationActionItem).filter(ContinuationActionItem.id == action_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Action item not found")

    check_project_access(act.project_id, current_user, db)

    act.is_completed = not act.is_completed
    act.completed_at = datetime.now(timezone.utc) if act.is_completed else None
    db.commit()
    db.refresh(act)
    return act

