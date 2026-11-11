import os
import sys
import uuid
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import SessionLocal, engine, Base
from app.models.all_models import (
    User, UserRole, Project, ProjectMembership, Document, Task,
    HandoverReport, ReportStatus, AuditLog, UserSession, PasswordResetToken,
    LoginAttempt, EmployeeProfile, ConflictItem
)
from app.core.config import settings, Settings
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    create_refresh_token, decode_access_token, decode_refresh_token,
    validate_password_strength, hash_token, generate_secure_random_token
)
from app.schemas.all_schemas import (
    UserRegister, UserLogin, RefreshTokenRequest, PasswordChangeRequest,
    PasswordForgotRequest, PasswordResetRequest, ProjectCreate, TaskCreate,
    AskProjectAIRequest
)
from app.api.auth import (
    register, login, refresh_token, logout, logout_all_sessions, change_password,
    forgot_password, reset_password
)
from app.api.employees import list_project_employees
from app.api.sources import list_project_sources
from app.api.conflicts import list_project_conflicts, ConflictResolveRequest
from app.api.ask_ai import ask_project_ai
from app.api.tasks import list_project_tasks, create_task
from app.api.analysis import trigger_project_reconstruction
from app.api.handovers import get_handover_report
from app.api.projects import get_global_audit_logs
from app.api.documents import validate_file_signature
from app.main import SecurityHeadersMiddleware

@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture(scope="function")
def admin_user(db_session: Session):
    admin = db_session.query(User).filter(User.email == "demo@continuum.ai").first()
    if not admin:
        admin = User(
            name="Continuum Demo Admin",
            email="demo@continuum.ai",
            password_hash=get_password_hash("password123"),
            role=UserRole.ADMIN.value,
            is_active=True
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
    return admin

# --- 1. Registration Privilege Escalation Protection ---
def test_privilege_escalation_blocked(db_session: Session):
    unique_email = f"attacker_{uuid.uuid4().hex[:6]}@continuum.ai"
    reg_data = UserRegister(
        name="Malicious Actor",
        email=unique_email,
        password="ValidPassword2025!",
        role="ADMIN"  # Attempt to escalate to ADMIN
    )
    resp = register(reg_data, db=db_session)
    user_in_db = db_session.query(User).filter(User.email == unique_email).first()
    
    assert user_in_db is not None
    assert user_in_db.role != UserRole.ADMIN.value, "Self-registration must not permit ADMIN role assignment"
    assert user_in_db.role == UserRole.TEAM_MEMBER.value
    assert resp["user"].role == UserRole.TEAM_MEMBER.value

# --- 2. Password Strength Validation ---
def test_password_strength_enforcement():
    weak_passwords = [
        "short1!",                # < 8 characters
        "alllowercase123!",       # Missing uppercase
        "ALLUPPERCASE123!",       # Missing lowercase
        "NoDigitsOrSpecialPass",  # Missing numbers/symbols
        "a" * 129                 # Exceeds max length bounds
    ]
    for weak in weak_passwords:
        with pytest.raises(ValueError):
            validate_password_strength(weak)

    # Valid strong password
    assert validate_password_strength("ValidP@ssw0rd2025") is True

# --- 3. Rate Limiting, Brute-Force Lockout & Generic 401 ---
def test_brute_force_lockout_and_generic_error(db_session: Session):
    target_email = f"victim_{uuid.uuid4().hex[:6]}@continuum.ai"
    reg = UserRegister(
        name="Victim User",
        email=target_email,
        password="CorrectPassword123!",
        role="TEAM_MEMBER"
    )
    register(reg, db=db_session)

    # 5 failed attempts
    for _ in range(5):
        with pytest.raises(HTTPException) as exc_info:
            login(UserLogin(email=target_email, password="WrongPassword!"), db=db_session)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid email or password."

    # 6th attempt: should trigger lockout
    with pytest.raises(HTTPException) as lockout_exc:
        login(UserLogin(email=target_email, password="WrongPassword!"), db=db_session)
    assert lockout_exc.value.status_code == 429
    assert "locked" in lockout_exc.value.detail.lower()

# --- 4. JWT Token Generation, Rotation, and Revocation Lifecycle ---
def test_jwt_session_rotation_and_revocation(db_session: Session):
    email = f"session_tester_{uuid.uuid4().hex[:6]}@continuum.ai"
    reg = UserRegister(
        name="Session Tester",
        email=email,
        password="SecurePassword2025!",
        role="TEAM_MEMBER"
    )
    resp = register(reg, db=db_session)
    access_token = resp["access_token"]
    refresh_jwt = resp["refresh_token"]

    # Verify access token structure
    access_payload = decode_access_token(access_token)
    assert access_payload is not None
    assert access_payload.get("type") == "access"
    assert "exp" in access_payload
    assert "jti" in access_payload

    # Rotate refresh token
    rotate_resp = refresh_token(RefreshTokenRequest(refresh_token=refresh_jwt), db=db_session)
    assert rotate_resp["access_token"] is not None
    new_refresh = rotate_resp["refresh_token"]
    assert new_refresh != refresh_jwt

    # Attempting to use old refresh token should now fail
    with pytest.raises(HTTPException) as old_token_exc:
        refresh_token(RefreshTokenRequest(refresh_token=refresh_jwt), db=db_session)
    assert old_token_exc.value.status_code == 401

    # Revoke session via logout
    user = db_session.query(User).filter(User.email == email).first()
    logout(current_user=user, db=db_session)

    # Refreshing after logout must fail
    with pytest.raises(HTTPException) as post_logout_exc:
        refresh_token(RefreshTokenRequest(refresh_token=new_refresh), db=db_session)
    assert post_logout_exc.value.status_code == 401

# --- 5. Password Reset Single-Use Token ---
def test_password_forgot_and_reset_token_single_use(db_session: Session):
    email = f"reset_user_{uuid.uuid4().hex[:6]}@continuum.ai"
    reg = UserRegister(
        name="Reset User",
        email=email,
        password="InitialPassword123!",
        role="TEAM_MEMBER"
    )
    register(reg, db=db_session)

    # Initiate reset
    forgot_resp = forgot_password(PasswordForgotRequest(email=email), db=db_session)
    reset_record = db_session.query(PasswordResetToken).order_by(PasswordResetToken.created_at.desc()).first()
    assert reset_record is not None
    assert reset_record.is_used is False

    raw_token = forgot_resp.get("dev_reset_token") or "test_raw_reset_token_value_123"
    reset_record.token_hash = hash_token(raw_token)
    db_session.commit()

    # Reset password with valid token
    reset_resp = reset_password(
        PasswordResetRequest(token=raw_token, new_password="BrandNewPassword2025!"),
        db=db_session
    )
    assert "successfully" in reset_resp["message"].lower()

    # Attempting to use the SAME token a second time must fail
    with pytest.raises(HTTPException) as reuse_exc:
        reset_password(
            PasswordResetRequest(token=raw_token, new_password="AnotherNewPassword2025!"),
            db=db_session
        )
    assert reuse_exc.value.status_code == 400
    assert "already been used" in reuse_exc.value.detail.lower() or "invalid" in reuse_exc.value.detail.lower()

# --- 6. Cross-Project Isolation & IDOR Protection ---
def test_cross_project_idor_protection(db_session: Session):
    # Owner User A & Project A
    user_a = User(
        name="Alice Owner",
        email=f"alice_{uuid.uuid4().hex[:4]}@continuum.ai",
        password_hash=get_password_hash("ValidPass123!"),
        role=UserRole.TEAM_MEMBER.value,
        is_active=True
    )
    # Unauthorized User B
    user_b = User(
        name="Bob Outsider",
        email=f"bob_{uuid.uuid4().hex[:4]}@continuum.ai",
        password_hash=get_password_hash("ValidPass123!"),
        role=UserRole.TEAM_MEMBER.value,
        is_active=True
    )
    db_session.add_all([user_a, user_b])
    db_session.commit()

    proj_a = Project(
        name="Confidential Project Alpha",
        description="Classified proprietary assets",
        owner_id=user_a.id,
        status="active"
    )
    db_session.add(proj_a)
    db_session.commit()

    # User B attempts to access Project A resources -> must receive 403 Forbidden
    with pytest.raises(HTTPException) as exc_tasks:
        list_project_tasks(proj_a.id, db=db_session, current_user=user_b)
    assert exc_tasks.value.status_code == 403

    with pytest.raises(HTTPException) as exc_emp:
        list_project_employees(proj_a.id, db=db_session, current_user=user_b)
    assert exc_emp.value.status_code == 403

    with pytest.raises(HTTPException) as exc_src:
        list_project_sources(proj_a.id, db=db_session, current_user=user_b)
    assert exc_src.value.status_code == 403

    with pytest.raises(HTTPException) as exc_conf:
        list_project_conflicts(proj_a.id, db=db_session, current_user=user_b)
    assert exc_conf.value.status_code == 403

    with pytest.raises(HTTPException) as exc_ai:
        ask_project_ai(AskProjectAIRequest(project_id=proj_a.id, question="What secrets?"), db=db_session, current_user=user_b)
    assert exc_ai.value.status_code == 403

# --- 7. Incoming Member Role Restrictions ---
def test_incoming_member_restrictions(db_session: Session):
    manager = User(
        name="Project Lead",
        email=f"lead_{uuid.uuid4().hex[:4]}@continuum.ai",
        password_hash=get_password_hash("ValidPass123!"),
        role=UserRole.PROJECT_MANAGER.value,
        is_active=True
    )
    incoming_user = User(
        name="Dave Incoming",
        email=f"dave_{uuid.uuid4().hex[:4]}@continuum.ai",
        password_hash=get_password_hash("ValidPass123!"),
        role=UserRole.INCOMING_MEMBER.value,
        is_active=True
    )
    db_session.add_all([manager, incoming_user])
    db_session.commit()

    proj = Project(
        name="Handover Beta",
        description="Transition test project",
        owner_id=manager.id,
        status="active"
    )
    db_session.add(proj)
    db_session.commit()

    membership = ProjectMembership(
        project_id=proj.id,
        user_id=incoming_user.id,
        role=UserRole.INCOMING_MEMBER.value
    )
    db_session.add(membership)
    db_session.commit()

    # 1. Incoming member cannot trigger knowledge reconstruction
    with pytest.raises(HTTPException) as exc_recon:
        trigger_project_reconstruction(proj.id, db=db_session, current_user=incoming_user)
    assert exc_recon.value.status_code == 403

    # 2. Incoming member cannot create tasks
    with pytest.raises(HTTPException) as exc_task_create:
        create_task(proj.id, TaskCreate(title="Unpermitted task"), db=db_session, current_user=incoming_user)
    assert exc_task_create.value.status_code == 403

    # 3. Incoming member cannot access unapproved handover reports
    draft_report = HandoverReport(
        project_id=proj.id,
        created_by=manager.id,
        title="Draft Report v1",
        report_content={},
        status=ReportStatus.PENDING_REVIEW.value,
        version=1
    )
    db_session.add(draft_report)
    db_session.commit()

    with pytest.raises(HTTPException) as exc_rep:
        get_handover_report(draft_report.id, db=db_session, current_user=incoming_user)
    assert exc_rep.value.status_code == 403
    assert "approved" in exc_rep.value.detail.lower()

    # 4. Incoming member CAN access approved handover reports
    draft_report.status = ReportStatus.APPROVED.value
    db_session.commit()

    approved_rep = get_handover_report(draft_report.id, db=db_session, current_user=incoming_user)
    assert approved_rep.id == draft_report.id

# --- 8. File Upload Magic Byte and Path Validation ---
def test_file_signature_validation():
    # Valid PDF signature
    assert validate_file_signature("pdf", b"%PDF-1.4 header contents") is True
    # Fake PDF (e.g. PE Windows binary)
    assert validate_file_signature("pdf", b"MZ\x90\x00\x03\x00\x00\x00") is False

    # Valid DOCX signature (PK zip)
    assert validate_file_signature("docx", b"PK\x03\x04\x14\x00") is True
    # Fake DOCX
    assert validate_file_signature("docx", b"NOT_A_ZIP_OR_DOCX") is False

    # Valid CSV / TXT / MD
    assert validate_file_signature("csv", b"id,name,value\n1,alpha,2") is True
    # Text file containing binary null bytes
    assert validate_file_signature("txt", b"some text\x00malicious_binary") is False

# --- 9. Admin Audit Logs RBAC Protection ---
def test_admin_audit_logs_rbac(db_session: Session, admin_user: User):
    regular_user = User(
        name="Regular Engineer",
        email=f"regular_{uuid.uuid4().hex[:4]}@continuum.ai",
        password_hash=get_password_hash("ValidPass123!"),
        role=UserRole.TEAM_MEMBER.value,
        is_active=True
    )
    db_session.add(regular_user)
    db_session.commit()

    # Regular user cannot read global audit logs
    from app.core.dependencies import require_role
    checker = require_role([UserRole.ADMIN.value])
    with pytest.raises(HTTPException) as exc_audit:
        checker(current_user=regular_user, db=db_session)
    assert exc_audit.value.status_code == 403

    # Admin user can read global audit logs
    admin_logs = get_global_audit_logs(page=1, page_size=10, db=db_session, current_user=admin_user)
    assert "total" in admin_logs
    assert "items" in admin_logs

# --- 10. Security Headers Middleware ---
def test_security_headers_middleware():
    from app.main import SecurityHeadersMiddleware, SECURITY_HEADERS

    headers_dict = {k.decode("utf-8").lower(): v.decode("utf-8") for k, v in SECURITY_HEADERS}

    assert headers_dict["x-content-type-options"] == "nosniff"
    assert headers_dict["x-frame-options"] == "DENY"
    assert headers_dict["x-xss-protection"] == "1; mode=block"
    assert headers_dict["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "default-src 'self'" in headers_dict["content-security-policy"]

    middleware = SecurityHeadersMiddleware(None)
    assert middleware.app is None

# --- 11. Production Startup Configuration Validation ---
def test_production_security_validation():
    # 1. Wildcard CORS blocked in production
    cors_bad = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="a" * 64,
        CORS_ORIGINS=["*"]
    )
    with pytest.raises(RuntimeError) as exc_cors:
        cors_bad.validate_production_security()
    assert "wildcard" in str(exc_cors.value).lower()

    # 2. Insecure default JWT secret blocked in production
    jwt_bad = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="insecure-default-change-me-in-production-continuum-ai-secret",
        CORS_ORIGINS=["https://continuum.ai"]
    )
    with pytest.raises(RuntimeError) as exc_jwt:
        jwt_bad.validate_production_security()
    assert "jwt_secret_key" in str(exc_jwt.value).lower()

# --- 12. CORS Origins Flexible Parsing & Optional Variables Tests ---
def test_cors_origins_parsing_formats():
    import os

    # A. Comma-separated string format (common in Render / env variables)
    os.environ["CORS_ORIGINS"] = "http://localhost:5173, http://127.0.0.1:5173, https://continuum-ai.onrender.com"
    try:
        s1 = Settings()
        assert isinstance(s1.CORS_ORIGINS, list)
        assert len(s1.CORS_ORIGINS) == 3
        assert "https://continuum-ai.onrender.com" in s1.CORS_ORIGINS
        assert "http://localhost:5173" in s1.CORS_ORIGINS
    finally:
        del os.environ["CORS_ORIGINS"]

    # B. JSON Array string format
    os.environ["CORS_ORIGINS"] = '["https://continuum-ai.onrender.com", "http://localhost:5173"]'
    try:
        s2 = Settings()
        assert isinstance(s2.CORS_ORIGINS, list)
        assert len(s2.CORS_ORIGINS) == 2
        assert "https://continuum-ai.onrender.com" in s2.CORS_ORIGINS
    finally:
        del os.environ["CORS_ORIGINS"]

    # C. Single string URL
    os.environ["CORS_ORIGINS"] = "https://continuum-ai.onrender.com"
    try:
        s3 = Settings()
        assert s3.CORS_ORIGINS == ["https://continuum-ai.onrender.com"]
    finally:
        del os.environ["CORS_ORIGINS"]

    # D. Missing optional environment variables do not crash startup
    s_default = Settings()
    assert s_default.AI_API_KEY == ""
    assert s_default.ENVIRONMENT in ["development", "production", "staging"]
    assert len(s_default.CORS_ORIGINS) >= 1

    # E. Render auto-whitelisting in production
    os.environ["RENDER_EXTERNAL_HOSTNAME"] = "continuum-ai.onrender.com"
    try:
        s_render = Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="a" * 64,
            CORS_ORIGINS=["http://localhost:5173"]
        )
        s_render.validate_production_security()
        assert "https://continuum-ai.onrender.com" in s_render.CORS_ORIGINS
    finally:
        del os.environ["RENDER_EXTERNAL_HOSTNAME"]

