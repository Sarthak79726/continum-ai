import os
import sys
import uuid
import pytest
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import SessionLocal, engine, Base
from app.models.all_models import (
    User, UserRole, Project, Document, DocumentChunk, Task, Decision, Risk,
    Dependency, Evidence, HandoverReport, Review, AuditLog, VerificationStatus
)
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.dependencies import check_project_access
from app.schemas.all_schemas import (
    UserRegister, UserLogin, ProjectCreate, ProjectUpdate, TaskCreate, TaskUpdate,
    HandoverCreate, ReviewCreate, EvidenceVerifyRequest, HandoverInitiateRequest,
    HandoverAcknowledgeRequest, AskProjectAIRequest
)
from app.api.auth import register, login
from app.api.projects import list_projects, create_project, get_project, update_project, delete_project, get_project_audit_logs
from app.api.tasks import list_project_tasks, create_task, update_task, delete_task
from app.api.evidence import get_project_evidence, update_evidence_status
from app.api.graph import get_project_knowledge_graph
from app.api.handovers import generate_handover_report, get_handover_report, approve_handover_report, reject_handover_report, export_handover_pdf
from app.api.settings import get_system_settings_status, update_system_settings, SettingsUpdate
from app.api.employees import (
    list_project_employees, get_employee_passport, reconstruct_employee_knowledge,
    initiate_employee_handover, acknowledge_employee_handover, toggle_continuation_action
)
from app.api.sources import list_project_sources
from app.api.conflicts import list_project_conflicts, resolve_conflict, ConflictResolveRequest
from app.api.ask_ai import ask_project_ai
from app.services.document_processor.pipeline import process_document_file
from app.services.sample_data.generator import generate_sample_files_on_disk, load_sample_dataset
from app.services.embeddings.embedding_service import get_embedding_function
from app.services.knowledge_extractor.extractor import KnowledgeExtractor
from app.services.evidence_verifier.verifier import EvidenceVerifier
from app.services.handover_generator.pdf_exporter import generate_handover_pdf
from app.services.vector_store.chroma_service import vector_store

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
            name="Demo Admin",
            email="demo@continuum.ai",
            password_hash=get_password_hash("password123"),
            role=UserRole.ADMIN.value,
            is_active=True
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
    return admin

def test_1_user_registration_and_login(db_session: Session):
    unique_email = f"engineer_{uuid.uuid4().hex[:6]}@continuum.ai"
    reg_data = UserRegister(
        name="Elena Rostova",
        email=unique_email,
        password="SecurePassword2025!",
        role="TEAM_MEMBER"
    )
    reg_resp = register(reg_data, db=db_session)
    assert reg_resp["access_token"] is not None
    assert reg_resp["user"].email == unique_email

    login_data = UserLogin(email=unique_email, password="SecurePassword2025!")
    login_resp = login(login_data, db=db_session)
    assert login_resp["access_token"] is not None
    assert login_resp["user"].name == "Elena Rostova"

def test_2_project_crud_and_cascade_delete(db_session: Session, admin_user: User):
    proj_in = ProjectCreate(
        name=f"Autonomous Drone Fleet {uuid.uuid4().hex[:4]}",
        description="Delivery network flight controller and telemetry unit",
        status="active"
    )
    created = create_project(proj_in, db=db_session, current_user=admin_user)
    assert created.id is not None
    assert "Autonomous Drone Fleet" in created.name

    upd_in = ProjectUpdate(status="completed")
    updated = update_project(created.id, upd_in, db=db_session, current_user=admin_user)
    assert updated.status == "completed"

    # Add task to verify cascade deletion
    t = Task(
        project_id=created.id,
        title="Calibrate IMU Sensors",
        description="Gyro and accelerometer calibration",
        status="pending"
    )
    db_session.add(t)
    db_session.commit()

    # Delete project
    delete_project(created.id, db=db_session, current_user=admin_user)

    # Verify task was cascade deleted
    orphaned_task = db_session.query(Task).filter(Task.project_id == created.id).first()
    assert orphaned_task is None, "Tasks should be cascade deleted when project is removed"

def test_3_document_parsers_pdf_docx_csv_txt():
    generate_sample_files_on_disk()

    # TXT parser
    txt_chunks = process_document_file("./data/sample_documents/meeting_notes.txt", "txt")
    assert len(txt_chunks) >= 1
    assert any("Rahul" in c["text"] for c in txt_chunks)

    # CSV parser
    csv_chunks = process_document_file("./data/sample_documents/task_status.csv", "csv")
    assert len(csv_chunks) >= 1
    assert any("TSK-" in c["text"] for c in csv_chunks)

    # PDF parser
    pdf_chunks = process_document_file("./data/sample_documents/project_overview.pdf", "pdf")
    assert len(pdf_chunks) >= 1
    assert any("CAMPUS" in c["text"].upper() for c in pdf_chunks)

    # DOCX parser
    docx_chunks = process_document_file("./data/sample_documents/technical_updates.docx", "docx")
    assert len(docx_chunks) >= 1
    assert any("Architecture" in c["text"] or "Payment" in c["text"] for c in docx_chunks)

def test_4_embedding_service_semantic_model():
    fn = get_embedding_function()
    vectors = fn([
        "Payment gateway integration with Stripe and Razorpay checkout API",
        "Billing microservice transactions and checkout processing",
        "Deep sea marine biology and coral reef restoration"
    ])
    assert len(vectors) == 3
    assert len(vectors[0]) == 384

    import numpy as np
    v1, v2, v3 = np.array(vectors[0]), np.array(vectors[1]), np.array(vectors[2])
    sim_related = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    sim_unrelated = float(np.dot(v1, v3) / (np.linalg.norm(v1) * np.linalg.norm(v3)))

    assert sim_related > sim_unrelated, "Related technical sentences should have higher cosine similarity than unrelated biology sentences"

def test_5_ai_knowledge_reconstruction_pipeline(db_session: Session, admin_user: User):
    proj = load_sample_dataset(db_session, admin_user)
    assert proj.id is not None

    extractor = KnowledgeExtractor(db_session, proj)
    result = extractor.run_reconstruction(admin_user.id)

    assert "completed_tasks" in result
    assert "ongoing_tasks" in result
    assert "pending_tasks" in result
    assert "important_decisions" in result
    assert "risks_and_blockers" in result
    assert "dependencies" in result

    tasks = db_session.query(Task).filter(Task.project_id == proj.id).all()
    assert len(tasks) >= 3

    decisions = db_session.query(Decision).filter(Decision.project_id == proj.id).all()
    assert len(decisions) >= 1

def test_6_evidence_verifier_grounding_rules(db_session: Session, admin_user: User):
    projects = list_projects(db=db_session, current_user=admin_user)
    assert len(projects) >= 1
    proj_id = projects[0].id

    verifier = EvidenceVerifier(db_session, proj_id)

    # 1. Unsupported claim with blank/unknown snippet must be UNVERIFIED
    unsupported = verifier.create_evidence_record(
        claim_text="Quantum encryption module was deployed to lunar satellite",
        source_snippet="Unknown",
        verification_status="VERIFIED"
    )
    assert unsupported.verification_status == VerificationStatus.UNVERIFIED.value
    assert unsupported.quality_label == "Insufficient Context"

    # 2. Grounded claim matching real document chunk text
    doc_chunk = db_session.query(DocumentChunk).filter(DocumentChunk.project_id == proj_id).first()
    assert doc_chunk is not None
    real_snippet = doc_chunk.extracted_text[:60]

    grounded = verifier.create_evidence_record(
        claim_text="Database architecture established",
        source_snippet=real_snippet,
        verification_status="NEEDS_REVIEW"
    )
    assert grounded.verification_status in [VerificationStatus.VERIFIED.value, VerificationStatus.NEEDS_REVIEW.value]
    assert grounded.chunk_id is not None

def test_7_evidence_verifier_conflicts_detection(db_session: Session):
    verifier = EvidenceVerifier(db_session, 1)
    task_items = [
        {"title": "Payment Gateway API", "status": "completed", "source_document": "sprint_1.txt"},
        {"title": "Payment Gateway API", "status": "blocked", "source_document": "meeting_notes.txt"}
    ]
    conflicts = verifier.detect_conflicts(task_items)
    assert len(conflicts) >= 1
    assert "Contradiction detected" in conflicts[0]["question"]

def test_8_knowledge_graph_generation(db_session: Session, admin_user: User):
    projects = list_projects(db=db_session, current_user=admin_user)
    proj_id = projects[0].id

    graph = get_project_knowledge_graph(proj_id, db=db_session, current_user=admin_user)
    assert len(graph.nodes) >= 3
    assert len(graph.edges) >= 2

    node_types = set(n.type for n in graph.nodes)
    assert "project" in node_types
    assert "task" in node_types

def test_9_handover_report_and_approval_workflow(db_session: Session, admin_user: User):
    projects = list_projects(db=db_session, current_user=admin_user)
    proj_id = projects[0].id

    ho_in = HandoverCreate(
        title="Comprehensive Production Handover Dossier",
        view_mode="incoming_member_view"
    )
    report = generate_handover_report(proj_id, ho_in, db=db_session, current_user=admin_user)
    assert report.id is not None
    assert report.status == "pending_review"

    rev_in = ReviewCreate(action="approved", comments="Verified all 14 handover sections against codebase.")
    approved = approve_handover_report(report.id, rev_in, db=db_session, current_user=admin_user)
    assert approved.status == "approved"
    assert len(approved.reviews) >= 1

def test_10_pdf_export_generation(db_session: Session, admin_user: User):
    projects = list_projects(db=db_session, current_user=admin_user)
    proj_id = projects[0].id
    reports = db_session.query(HandoverReport).filter(HandoverReport.project_id == proj_id).all()
    assert len(reports) >= 1

    pdf_buffer = generate_handover_pdf(reports[0].report_content)
    pdf_bytes = pdf_buffer.getvalue()
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")

def test_11_rbac_and_project_isolation(db_session: Session):
    u1 = User(name="User A", email=f"usera_{uuid.uuid4().hex[:4]}@org.com", password_hash="hash", role="TEAM_MEMBER")
    u2 = User(name="User B", email=f"userb_{uuid.uuid4().hex[:4]}@org.com", password_hash="hash", role="TEAM_MEMBER")
    db_session.add_all([u1, u2])
    db_session.commit()

    p_a = Project(name="User A Private Project", owner_id=u1.id, status="active")
    db_session.add(p_a)
    db_session.commit()

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        check_project_access(p_a.id, u2, db_session)
    assert exc.value.status_code == 403

def test_12_settings_and_audit_logs(db_session: Session, admin_user: User):
    upd = SettingsUpdate(ai_provider="demo", ai_model="all-MiniLM-L6-v2")
    res = update_system_settings(upd, current_user=admin_user)
    assert res["status"] == "success"

    status_data = get_system_settings_status(current_user=admin_user)
    assert status_data["ai_engine"]["provider"] == "demo"

    projects = list_projects(db=db_session, current_user=admin_user)
    proj_id = projects[0].id
    logs = get_project_audit_logs(proj_id, db=db_session, current_user=admin_user)
    assert len(logs) >= 1
    assert any("RECONSTRUCTION" in log["action"] or "PROJECT" in log["action"] for log in logs)

def test_13_employee_passport_and_reconstruction(db_session: Session, admin_user: User):
    projects = list_projects(db=db_session, current_user=admin_user)
    proj_id = projects[0].id
    employees = list_project_employees(proj_id, db=db_session, current_user=admin_user)
    assert len(employees) >= 1

    rahul = next((e for e in employees if "rahul" in e.name.lower()), employees[0])
    passport = get_employee_passport(rahul.id, db=db_session, current_user=admin_user)

    assert passport["employee"].id == rahul.id
    assert len(passport["commits"]) >= 1
    assert len(passport["api_endpoints"]) >= 1
    assert len(passport["bugs_and_debt"]) >= 1
    assert len(passport["blockers"]) >= 1
    assert len(passport["continuation_plan"]) >= 1

def test_14_handover_initiation_and_acknowledgement(db_session: Session, admin_user: User):
    projects = list_projects(db=db_session, current_user=admin_user)
    proj_id = projects[0].id
    employees = list_project_employees(proj_id, db=db_session, current_user=admin_user)
    rahul = next((e for e in employees if "rahul" in e.name.lower()), employees[0])
    maya = next((e for e in employees if "maya" in e.name.lower()), employees[-1])

    # Initiate handover
    req_init = HandoverInitiateRequest(
        departing_employee_id=rahul.id,
        successor_id=maya.id,
        notes="Transitioning backend core token revocation and bulk endpoints"
    )
    init_res = initiate_employee_handover(rahul.id, req_init, db=db_session, current_user=admin_user)
    assert init_res["status"] == "success"

    # Successor acknowledges handover
    req_ack = HandoverAcknowledgeRequest(
        comments="Formally accepted custody of auth services and attendance schema"
    )
    ack_res = acknowledge_employee_handover(rahul.id, req_ack, db=db_session, current_user=admin_user)
    assert ack_res["status"] == "success"
    assert ack_res["acknowledged_at"] is not None

    # Toggle a checklist item
    passport = get_employee_passport(rahul.id, db=db_session, current_user=admin_user)
    if passport["continuation_plan"]:
        first_item = passport["continuation_plan"][0]
        initial_completed = first_item.is_completed
        toggled = toggle_continuation_action(first_item.id, db=db_session, current_user=admin_user)
        assert toggled.is_completed != initial_completed

def test_15_source_connection_and_conflicts(db_session: Session, admin_user: User):
    projects = list_projects(db=db_session, current_user=admin_user)
    proj_id = projects[0].id

    sources = list_project_sources(proj_id, db=db_session, current_user=admin_user)
    assert len(sources) >= 1
    assert sources[0].source_type == "github"

    conflicts = list_project_conflicts(proj_id, db=db_session, current_user=admin_user)
    assert len(conflicts) >= 1

    open_conflict = next((c for c in conflicts if c.resolution_status == "open"), conflicts[0])
    resolved = resolve_conflict(
        open_conflict.id,
        ConflictResolveRequest(resolution_notes="Authoritative verdict: Redis connection is failing under load. Kept ticket open."),
        db=db_session,
        current_user=admin_user
    )
    assert resolved.resolution_status == "resolved"
    assert resolved.resolved_by == admin_user.name

def test_16_ask_project_ai_grounded_rag(db_session: Session, admin_user: User):
    projects = list_projects(db=db_session, current_user=admin_user)
    proj_id = projects[0].id
    employees = list_project_employees(proj_id, db=db_session, current_user=admin_user)
    rahul = next((e for e in employees if "rahul" in e.name.lower()), employees[0])

    # Ask question about active bugs and technical debt
    req = AskProjectAIRequest(
        project_id=proj_id,
        question="What are the active unresolved bugs and technical debt items?",
        employee_id=rahul.id,
        role_scope="BACKEND"
    )
    ans = ask_project_ai(req, db=db_session, current_user=admin_user)
    assert ans["confidence"] in ["HIGH", "MEDIUM", "LOW", "INSUFFICIENT_EVIDENCE"]
    assert len(ans["citations"]) >= 1
    assert any("bug" in ans["answer"].lower() or "debt" in ans["answer"].lower() or "unresolved" in ans["answer"].lower() for _ in [1])

