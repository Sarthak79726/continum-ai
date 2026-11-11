import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.config import settings
from app.core.security import (
    get_password_hash,
    verify_password,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    generate_secure_random_token,
    hash_token
)
from app.core.dependencies import get_current_user
from app.models.all_models import (
    User, UserRole, UserSession, PasswordResetToken, LoginAttempt, AuditLog
)
from app.schemas.all_schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    Token,
    RefreshTokenRequest,
    PasswordChangeRequest,
    PasswordForgotRequest,
    PasswordResetRequest,
    UserSessionResponse
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

def get_client_ip(request: Request = None) -> str:
    """Safely extracts client IP address."""
    if not request:
        return "127.0.0.1"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

def get_user_agent(request: Request = None) -> str:
    """Safely extracts client user agent."""
    if not request:
        return "Unknown Device"
    return request.headers.get("User-Agent", "Unknown Device")[:255]

def is_expired(dt: datetime) -> bool:
    """Safely checks if a datetime is expired, handling both timezone-aware and naive timestamps."""
    if not dt:
        return True
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt < datetime.now(timezone.utc)

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, request: Request = None, db: Session = Depends(get_db)):
    """
    Secure user registration:
    - Enforces email syntax validation
    - Enforces strong password complexity (8+ chars, upper, lower, numbers/symbols, max 128 chars)
    - Prevents privilege escalation: Public registration CANNOT grant ADMIN or PROJECT_MANAGER
    - Issues short-lived access token and rotating refresh token session
    """
    email_clean = user_in.email.strip().lower()
    if not re.match(EMAIL_REGEX, email_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address format."
        )

    # Check for duplicate user
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Password strength check
    try:
        validate_password_strength(user_in.password)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )

    # Prevent privilege escalation: public registration defaults to least-privilege TEAM_MEMBER
    # Even if client sends "ADMIN", it is strictly ignored.
    role_val = UserRole.TEAM_MEMBER.value
    if user_in.role and user_in.role.upper() == UserRole.INCOMING_MEMBER.value:
        role_val = UserRole.INCOMING_MEMBER.value

    hashed_pw = get_password_hash(user_in.password)
    user = User(
        name=user_in.name.strip(),
        email=email_clean,
        password_hash=hashed_pw,
        role=role_val,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Log registration in Audit Log
    audit = AuditLog(
        user_id=user.id,
        action="USER_REGISTERED",
        details=f"User '{user.name}' ({user.email}) registered with role {user.role}."
    )
    db.add(audit)

    # Generate token pair
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    raw_refresh = generate_secure_random_token(48)
    refresh_jwt = create_refresh_token({"sub": str(user.id), "session_token": raw_refresh})

    # Save session
    ip = get_client_ip(request)
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_token(raw_refresh),
        device_info=get_user_agent(request),
        ip_address=ip,
        is_revoked=False,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "refresh_token": refresh_jwt
    }

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, request: Request = None, db: Session = Depends(get_db)):
    """
    Secure login endpoint:
    - Enforces rate limiting against brute force attacks (locks out after consecutive failures)
    - Emits generic error messages to prevent username/email enumeration
    - Issues short-lived access token (30 mins) and trackable refresh token session
    """
    email_clean = login_data.email.strip().lower()
    ip = get_client_ip(request)

    # Check brute-force lockout window
    window_start = datetime.now(timezone.utc) - timedelta(minutes=settings.LOCKOUT_MINUTES)
    recent_failures = db.query(LoginAttempt).filter(
        LoginAttempt.email == email_clean,
        LoginAttempt.success == False,
        LoginAttempt.attempted_at >= window_start
    ).count()

    if recent_failures >= settings.MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked due to multiple failed login attempts. Please try again after {settings.LOCKOUT_MINUTES} minutes."
        )

    user = db.query(User).filter(User.email == email_clean).first()
    is_valid = user and verify_password(login_data.password, user.password_hash)

    if not is_valid:
        # Record failed attempt
        attempt = LoginAttempt(
            email=email_clean,
            ip_address=ip,
            success=False
        )
        db.add(attempt)
        db.commit()
        # Generic message prevents account enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated. Please contact your system administrator."
        )

    # Record successful attempt
    attempt = LoginAttempt(
        email=email_clean,
        ip_address=ip,
        success=True
    )
    db.add(attempt)

    audit = AuditLog(
        user_id=user.id,
        action="USER_LOGIN_SUCCESS",
        details=f"User '{user.email}' logged in from IP {ip}."
    )
    db.add(audit)

    # Generate token pair
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    raw_refresh = generate_secure_random_token(48)
    refresh_jwt = create_refresh_token({"sub": str(user.id), "session_token": raw_refresh})

    # Save session
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_token(raw_refresh),
        device_info=get_user_agent(request),
        ip_address=ip,
        is_revoked=False,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "refresh_token": refresh_jwt
    }

@router.post("/refresh", response_model=Token)
def refresh_token(req: RefreshTokenRequest, request: Request = None, db: Session = Depends(get_db)):
    """
    Refresh token rotation:
    - Validates refresh token signature & expiration
    - Verifies session is not revoked in the database
    - Rotates the session with a new refresh token (invalidating the old one)
    - Returns newly minted access token and rotated refresh token
    """
    payload = decode_refresh_token(req.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )

    user_id = int(payload["sub"])
    raw_token = payload.get("session_token")
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed refresh token structure."
        )

    token_h = hash_token(raw_token)
    session = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.refresh_token_hash == token_h
    ).first()

    if not session or session.is_revoked or is_expired(session.expires_at):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or was revoked. Please log in again."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive."
        )

    # Rotate refresh token: generate new one and update session
    new_raw_refresh = generate_secure_random_token(48)
    new_refresh_jwt = create_refresh_token({"sub": str(user.id), "session_token": new_raw_refresh})
    new_access_token = create_access_token({"sub": str(user.id), "role": user.role})

    session.refresh_token_hash = hash_token(new_raw_refresh)
    session.last_used_at = datetime.now(timezone.utc)
    session.ip_address = get_client_ip(request)
    db.commit()

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "user": user,
        "refresh_token": new_refresh_jwt
    }

@router.post("/logout")
def logout(
    req: Optional[RefreshTokenRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revokes the active refresh token session for the user upon sign-out.
    """
    if req and req.refresh_token:
        payload = decode_refresh_token(req.refresh_token)
        if payload and payload.get("session_token"):
            token_h = hash_token(payload["session_token"])
            db.query(UserSession).filter(
                UserSession.user_id == current_user.id,
                UserSession.refresh_token_hash == token_h
            ).update({"is_revoked": True})
            db.commit()
    else:
        # Revoke the most recent active session
        latest = db.query(UserSession).filter(
            UserSession.user_id == current_user.id,
            UserSession.is_revoked == False
        ).order_by(UserSession.last_used_at.desc()).first()
        if latest:
            latest.is_revoked = True
            db.commit()

    audit = AuditLog(
        user_id=current_user.id,
        action="USER_LOGOUT",
        details=f"User '{current_user.email}' logged out."
    )
    db.add(audit)
    db.commit()

    return {"status": "success", "message": "Successfully logged out and session revoked."}

@router.post("/logout-all")
def logout_all_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revokes ALL active sessions across all devices for the current user.
    """
    db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_revoked == False
    ).update({"is_revoked": True})

    audit = AuditLog(
        user_id=current_user.id,
        action="USER_LOGOUT_ALL_DEVICES",
        details=f"User '{current_user.email}' revoked all active sessions across all devices."
    )
    db.add(audit)
    db.commit()

    return {"status": "success", "message": "All sessions across all devices have been revoked."}

@router.get("/sessions", response_model=List[UserSessionResponse])
def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists all active and historical sessions for the current user."""
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id
    ).order_by(UserSession.last_used_at.desc()).limit(20).all()
    return sessions

@router.delete("/sessions/{session_id}")
def revoke_specific_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allows a user to selectively revoke a session on an individual device."""
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    session.is_revoked = True
    db.commit()
    return {"status": "success", "message": "Session revoked."}

@router.post("/change-password")
def change_password(
    req: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Authenticated password change:
    - Verifies existing password
    - Validates new password complexity
    - Updates hash and invalidates all existing sessions
    """
    if not verify_password(req.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed."
        )

    try:
        validate_password_strength(req.new_password)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    current_user.password_hash = get_password_hash(req.new_password)

    # Invalidate all active sessions on password change
    db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_revoked == False
    ).update({"is_revoked": True})

    audit = AuditLog(
        user_id=current_user.id,
        action="PASSWORD_CHANGED",
        details=f"User '{current_user.email}' updated their account password. All active sessions revoked."
    )
    db.add(audit)
    db.commit()

    return {"status": "success", "message": "Password changed successfully. Please log in with your new password."}

@router.post("/forgot-password")
def forgot_password(req: PasswordForgotRequest, db: Session = Depends(get_db)):
    """
    Initiates password reset:
    - Generates single-use, 15-minute token
    - Hashes token before storing in database
    - Always returns generic message to prevent account enumeration
    """
    email_clean = req.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()

    if user and user.is_active:
        raw_reset_token = generate_secure_random_token(48)
        hashed_reset = hash_token(raw_reset_token)

        # Invalidate any prior unused reset tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False
        ).update({"is_used": True})

        reset_entry = PasswordResetToken(
            user_id=user.id,
            token_hash=hashed_reset,
            is_used=False,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        )
        db.add(reset_entry)

        audit = AuditLog(
            user_id=user.id,
            action="PASSWORD_RESET_REQUESTED",
            details=f"Password reset token issued for '{user.email}'. Token expires in {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} mins."
        )
        db.add(audit)
        db.commit()

        # In a production environment with SMTP configured, this would dispatch an email.
        # For evaluation/demo and testing purposes without an external mail server, we return instructions or token in dev mode
        if settings.ENVIRONMENT.lower() == "development":
            return {
                "status": "success",
                "message": "If that email address is registered, password reset instructions have been sent.",
                "dev_reset_token": raw_reset_token  # Provided only in development mode for automated test suites
            }

    return {
        "status": "success",
        "message": "If that email address is registered, password reset instructions have been sent."
    }

@router.post("/reset-password")
def reset_password(req: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Completes password reset:
    - Hashes supplied token and finds active single-use record
    - Enforces new password complexity
    - Marks token used and invalidates all existing user sessions
    """
    hashed_token = hash_token(req.token.strip())
    reset_entry = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == hashed_token
    ).first()

    if not reset_entry or reset_entry.is_used or is_expired(reset_entry.expires_at):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token is invalid, expired, or has already been used."
        )

    try:
        validate_password_strength(req.new_password)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    user = db.query(User).filter(User.id == reset_entry.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="User account is invalid or deactivated.")

    # Update password and mark token used
    user.password_hash = get_password_hash(req.new_password)
    reset_entry.is_used = True

    # Revoke all existing sessions for security
    db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.is_revoked == False
    ).update({"is_revoked": True})

    audit = AuditLog(
        user_id=user.id,
        action="PASSWORD_RESET_COMPLETED",
        details=f"User '{user.email}' successfully reset their password via single-use token. All sessions revoked."
    )
    db.add(audit)
    db.commit()

    return {"status": "success", "message": "Password successfully reset. You may now log in with your new password."}

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user
