from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.security import decode_access_token
from app.models.all_models import User, Project, ProjectMembership, UserRole, AuditLog

security_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates the bearer access token and returns the authenticated User.
    Rejects missing, expired, invalid, or deactivated user accounts.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier.",
        )
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account no longer exists.",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact your system administrator.",
        )
        
    return user

def require_role(allowed_roles: List[str]):
    """
    Dependency checking global user roles (e.g. ADMIN).
    """
    def role_checker(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        if current_user.role == UserRole.ADMIN.value:
            return current_user
        if current_user.role not in allowed_roles:
            audit = AuditLog(
                user_id=current_user.id,
                action="ACCESS_DENIED_ROLE",
                details=f"User {current_user.email} (role: {current_user.role}) denied access. Required: {allowed_roles}."
            )
            db.add(audit)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Required role in {allowed_roles}."
            )
        return current_user
    return role_checker

def check_project_access(
    project_id: int,
    user: User,
    db: Session,
    allowed_roles: Optional[List[str]] = None
) -> Project:
    """
    Strict Tenant & Project Isolation Guard:
    1. Looks up project by ID.
    2. Allows global ADMIN full access.
    3. Allows Project Owner (treated as PROJECT_MANAGER).
    4. Checks explicit ProjectMembership.
    5. Validates role permissions if allowed_roles is specified.
    6. Logs ACCESS_DENIED audit entry upon unauthorized access attempts.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found."
        )
    
    # Global admin has full access across all projects
    if user.role == UserRole.ADMIN.value:
        return project

    # Project owner has PROJECT_MANAGER privileges for this project
    if project.owner_id == user.id:
        if allowed_roles and UserRole.PROJECT_MANAGER.value not in allowed_roles and UserRole.ADMIN.value in allowed_roles and len(allowed_roles) == 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Action restricted to global administrators."
            )
        return project

    # Check project membership
    membership = db.query(ProjectMembership).filter(
        ProjectMembership.project_id == project_id,
        ProjectMembership.user_id == user.id
    ).first()

    if not membership:
        audit = AuditLog(
            user_id=user.id,
            project_id=project_id,
            action="ACCESS_DENIED_PROJECT_ISOLATION",
            details=f"User {user.email} attempted unauthorized access to Project {project_id} without membership."
        )
        db.add(audit)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not an authorized member of this project."
        )

    user_effective_role = membership.role or user.role
    if allowed_roles and user_effective_role not in allowed_roles:
        audit = AuditLog(
            user_id=user.id,
            project_id=project_id,
            action="ACCESS_DENIED_INSUFFICIENT_PROJECT_ROLE",
            details=f"User {user.email} with project role '{user_effective_role}' attempted action requiring {allowed_roles}."
        )
        db.add(audit)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Insufficient project permissions. Required role: {allowed_roles}."
        )

    return project
