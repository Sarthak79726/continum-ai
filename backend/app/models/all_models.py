import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean, JSON, Float
from sqlalchemy.orm import relationship
from app.database.session import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    PROJECT_MANAGER = "PROJECT_MANAGER"
    TEAM_MEMBER = "TEAM_MEMBER"
    INCOMING_MEMBER = "INCOMING_MEMBER"

class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

class VerificationStatus(str, enum.Enum):
    VERIFIED = "VERIFIED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CONFLICTING = "CONFLICTING"
    UNVERIFIED = "UNVERIFIED"

class TaskStatus(str, enum.Enum):
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    BLOCKED = "blocked"

class PriorityLevel(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ReportStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"

class HandoverLifecycleStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    HANDOVER_INITIATED = "HANDOVER_INITIATED"
    ANALYSING = "ANALYSING"
    EVIDENCE_REVIEW = "EVIDENCE_REVIEW"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    SHARED = "SHARED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    COMPLETED = "COMPLETED"

class BugClassification(str, enum.Enum):
    CONFIRMED_UNRESOLVED = "CONFIRMED UNRESOLVED"
    POTENTIAL_BUG = "POTENTIAL BUG"
    NEEDS_INVESTIGATION = "NEEDS INVESTIGATION"
    RESOLVED = "RESOLVED"
    UNVERIFIED = "UNVERIFIED"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.TEAM_MEMBER.value, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    projects = relationship("Project", back_populates="owner")
    memberships = relationship("ProjectMembership", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="uploader")
    reviews = relationship("Review", back_populates="reviewer")
    reports = relationship("HandoverReport", back_populates="creator")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token_hash = Column(String(255), unique=True, index=True, nullable=False)
    device_info = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="sessions")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, index=True, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="password_resets")

class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), index=True, nullable=False)
    ip_address = Column(String(50), nullable=True)
    success = Column(Boolean, default=False, nullable=False)
    attempted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="active", nullable=False)  # active, completed, archived
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="projects")
    memberships = relationship("ProjectMembership", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="project", cascade="all, delete-orphan")
    knowledge = relationship("ExtractedKnowledge", back_populates="project", cascade="all, delete-orphan")
    evidence_items = relationship("Evidence", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="project", cascade="all, delete-orphan")
    dependencies = relationship("Dependency", back_populates="project", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="project", cascade="all, delete-orphan")
    handovers = relationship("HandoverReport", back_populates="project", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="project", cascade="all, delete-orphan")
    employees = relationship("EmployeeProfile", back_populates="project", cascade="all, delete-orphan")
    commits = relationship("CommitRecord", back_populates="project", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequestRecord", back_populates="project", cascade="all, delete-orphan")
    api_endpoints = relationship("APIEndpointRecord", back_populates="project", cascade="all, delete-orphan")
    schema_records = relationship("DatabaseSchemaRecord", back_populates="project", cascade="all, delete-orphan")
    bugs_and_debt = relationship("BugDebtItem", back_populates="project", cascade="all, delete-orphan")
    blockers = relationship("BlockerItem", back_populates="project", cascade="all, delete-orphan")
    knowledge_gaps = relationship("KnowledgeGapItem", back_populates="project", cascade="all, delete-orphan")
    timeline_events = relationship("WorkTimelineEvent", back_populates="project", cascade="all, delete-orphan")
    continuation_actions = relationship("ContinuationActionItem", back_populates="project", cascade="all, delete-orphan")
    conflicts = relationship("ConflictItem", back_populates="project", cascade="all, delete-orphan")
    source_connections = relationship("SourceConnection", back_populates="project", cascade="all, delete-orphan")

class ProjectMembership(Base):
    __tablename__ = "project_memberships"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(50), default=UserRole.TEAM_MEMBER.value, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="memberships")
    user = relationship("User", back_populates="memberships")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx, txt, csv
    file_size = Column(Integer, default=0)
    storage_path = Column(String(500), nullable=False)
    processing_status = Column(String(50), default=DocumentStatus.UPLOADED.value, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="documents")
    uploader = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    evidence_items = relationship("Evidence", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    section_title = Column(String(255), nullable=True)
    extracted_text = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="chunks")
    project = relationship("Project", back_populates="chunks")

class ExtractedKnowledge(Base):
    __tablename__ = "extracted_knowledge"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    category = Column(String(100), nullable=False)  # overview, completed_tasks, ongoing_tasks, pending_tasks, decisions, risks, dependencies, questions
    structured_content = Column(JSON, nullable=False)
    verification_status = Column(String(50), default=VerificationStatus.NEEDS_REVIEW.value, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="knowledge")

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_id = Column(Integer, ForeignKey("extracted_knowledge.id"), nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    chunk_id = Column(Integer, ForeignKey("document_chunks.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    claim_text = Column(Text, nullable=False)
    source_snippet = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    verification_status = Column(String(50), default=VerificationStatus.NEEDS_REVIEW.value, nullable=False)
    quality_label = Column(String(50), default="Direct Citation", nullable=False)  # Direct Citation, Inferred, Conflicting, Insufficient Context
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="evidence_items")
    document = relationship("Document", back_populates="evidence_items")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default=TaskStatus.PENDING.value, nullable=False)
    priority = Column(String(50), default=PriorityLevel.MEDIUM.value, nullable=False)
    owner = Column(String(100), default="Unassigned")
    due_date = Column(String(50), nullable=True)
    source_reference = Column(String(255), nullable=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=True)
    is_recommendation = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="tasks")

class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=True)
    date_decided = Column(String(50), nullable=True)
    source_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="decisions")

class Dependency(Base):
    __tablename__ = "dependencies"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    source_title = Column(String(255), nullable=False)
    target_title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    evidence = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="dependencies")

class Risk(Base):
    __tablename__ = "risks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(50), default=PriorityLevel.MEDIUM.value, nullable=False)
    status = Column(String(50), default="active", nullable=False)
    impact = Column(Text, nullable=True)
    suggested_resolution = Column(Text, nullable=True)
    source_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="risks")

class HandoverReport(Base):
    __tablename__ = "handover_reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    report_content = Column(JSON, nullable=False)
    status = Column(String(50), default=ReportStatus.DRAFT.value, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    view_mode = Column(String(50), default="incoming_member_view")  # pm_view or incoming_member_view
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    departing_employee_id = Column(Integer, nullable=True)
    successor_id = Column(Integer, nullable=True)
    lifecycle_status = Column(String(50), default=HandoverLifecycleStatus.ACTIVE.value, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledgement_notes = Column(Text, nullable=True)

    project = relationship("Project", back_populates="handovers")
    creator = relationship("User", back_populates="reports")
    reviews = relationship("Review", back_populates="report", cascade="all, delete-orphan")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("handover_reports.id"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)  # approved, rejected, revision_requested
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    report = relationship("HandoverReport", back_populates="reviews")
    reviewer = relationship("User", back_populates="reviews")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    project = relationship("Project", back_populates="audit_logs")

# --- EMPLOYEE KNOWLEDGE PASSPORT & CODE CONTRIBUTION MODELS ---

class EmployeeProfile(Base):
    __tablename__ = "employee_profiles"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(100), nullable=False)
    employee_id_code = Column(String(50), nullable=True)
    role_title = Column(String(100), nullable=False)
    department = Column(String(100), default="Engineering")
    responsibilities = Column(JSON, default=list)
    date_joined = Column(String(50), nullable=True)
    handover_initiation_date = Column(String(50), nullable=True)
    assigned_successor_id = Column(Integer, ForeignKey("employee_profiles.id"), nullable=True)
    handover_status = Column(String(50), default=HandoverLifecycleStatus.ACTIVE.value, nullable=False)
    last_activity_date = Column(String(50), nullable=True)
    contribution_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="employees")
    user = relationship("User")
    commits = relationship("CommitRecord", back_populates="employee", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequestRecord", back_populates="employee", cascade="all, delete-orphan")
    api_endpoints = relationship("APIEndpointRecord", back_populates="employee", cascade="all, delete-orphan")
    schema_records = relationship("DatabaseSchemaRecord", back_populates="employee", cascade="all, delete-orphan")
    bugs = relationship("BugDebtItem", back_populates="employee", cascade="all, delete-orphan")
    blockers = relationship("BlockerItem", back_populates="employee", cascade="all, delete-orphan")
    knowledge_gaps = relationship("KnowledgeGapItem", back_populates="employee", cascade="all, delete-orphan")
    timeline_events = relationship("WorkTimelineEvent", back_populates="employee", cascade="all, delete-orphan")

class CommitRecord(Base):
    __tablename__ = "commit_records"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employee_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    commit_hash = Column(String(64), nullable=False, index=True)
    message = Column(Text, nullable=False)
    branch = Column(String(100), default="main")
    changed_files = Column(JSON, default=list)
    insertions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    is_merged = Column(Boolean, default=True)
    has_tests = Column(Boolean, default=False)
    affected_modules = Column(JSON, default=list)
    timestamp = Column(String(50), nullable=True)
    source_url = Column(String(500), nullable=True)

    project = relationship("Project", back_populates="commits")
    employee = relationship("EmployeeProfile", back_populates="commits")

class PullRequestRecord(Base):
    __tablename__ = "pull_request_records"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employee_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    pr_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source_branch = Column(String(100), nullable=False)
    target_branch = Column(String(100), default="main")
    is_merged = Column(Boolean, default=False)
    has_tests = Column(Boolean, default=False)
    open_review_comments = Column(Integer, default=0)
    review_notes = Column(Text, nullable=True)
    timestamp = Column(String(50), nullable=True)
    source_url = Column(String(500), nullable=True)

    project = relationship("Project", back_populates="pull_requests")
    employee = relationship("EmployeeProfile", back_populates="pull_requests")

class APIEndpointRecord(Base):
    __tablename__ = "api_endpoint_records"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employee_profiles.id", ondelete="CASCADE"), nullable=True, index=True)
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE, PATCH
    endpoint_path = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    backend_module = Column(String(100), nullable=False)
    request_params = Column(JSON, default=dict)
    request_body = Column(JSON, default=dict)
    response_structure = Column(JSON, default=dict)
    auth_required = Column(Boolean, default=True)
    permissions_required = Column(String(100), default="Authenticated")
    database_tables = Column(JSON, default=list)
    frontend_callers = Column(JSON, default=list)
    test_coverage_status = Column(String(50), default="MISSING_TESTS")  # COVERED, MISSING_TESTS, PARTIALLY_TESTED
    implementation_status = Column(String(50), default="COMPLETED")  # COMPLETED, PARTIALLY_IMPLEMENTED, NOT_IMPLEMENTED, NEEDS_TESTING
    source_reference = Column(String(255), nullable=True)
    last_modified = Column(String(50), nullable=True)

    project = relationship("Project", back_populates="api_endpoints")
    employee = relationship("EmployeeProfile", back_populates="api_endpoints")

class DatabaseSchemaRecord(Base):
    __tablename__ = "database_schema_records"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employee_profiles.id", ondelete="CASCADE"), nullable=True, index=True)
    model_name = Column(String(100), nullable=False)
    table_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    columns = Column(JSON, default=list)
    relationships = Column(JSON, default=list)
    foreign_keys = Column(JSON, default=list)
    indexes = Column(JSON, default=list)
    migration_script = Column(String(100), nullable=True)
    is_pending = Column(Boolean, default=False)
    dependent_modules = Column(JSON, default=list)

    project = relationship("Project", back_populates="schema_records")
    employee = relationship("EmployeeProfile", back_populates="schema_records")

class BugDebtItem(Base):
    __tablename__ = "bug_debt_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employee_profiles.id", ondelete="CASCADE"), nullable=True, index=True)
    issue_code = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    classification = Column(String(50), default=BugClassification.CONFIRMED_UNRESOLVED.value, nullable=False)
    severity = Column(String(50), default=PriorityLevel.MEDIUM.value, nullable=False)
    priority = Column(String(50), default=PriorityLevel.MEDIUM.value, nullable=False)
    affected_module = Column(String(100), nullable=False)
    file_path = Column(String(255), nullable=True)
    line_number = Column(Integer, nullable=True)
    evidence_snippet = Column(Text, nullable=True)
    investigation_performed = Column(Text, nullable=True)
    fixes_attempted = Column(Text, nullable=True)
    why_unresolved = Column(Text, nullable=True)
    recommended_next_action = Column(Text, nullable=True)
    confidence_level = Column(String(50), default="HIGH")  # HIGH, MEDIUM, LOW
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="bugs_and_debt")
    employee = relationship("EmployeeProfile", back_populates="bugs")

class BlockerItem(Base):
    __tablename__ = "blocker_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employee_profiles.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    failed_attempts = Column(Text, nullable=True)
    external_dependency = Column(Text, nullable=True)
    required_assistance = Column(Text, nullable=True)
    status = Column(String(50), default="active")  # active, resolved
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="blockers")
    employee = relationship("EmployeeProfile", back_populates="blockers")

class KnowledgeGapItem(Base):
    __tablename__ = "knowledge_gap_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employee_profiles.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)  # missing_documentation, api_without_specs, code_without_tests, undocumented_dependency, decision_without_reasoning, unclear_ownership
    description = Column(Text, nullable=False)
    affected_component = Column(String(100), nullable=True)
    severity = Column(String(50), default="medium")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="knowledge_gaps")
    employee = relationship("EmployeeProfile", back_populates="knowledge_gaps")

class WorkTimelineEvent(Base):
    __tablename__ = "work_timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employee_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(String(50), nullable=False)
    event_type = Column(String(50), nullable=False)  # task_completed, task_started, commit_created, pr_opened, pr_merged, bug_reported, bug_fixed, decision_made, blocker_encountered, meeting_held
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source_reference = Column(String(255), nullable=True)
    verification_status = Column(String(50), default=VerificationStatus.VERIFIED.value)
    source_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="timeline_events")
    employee = relationship("EmployeeProfile", back_populates="timeline_events")

class ContinuationActionItem(Base):
    __tablename__ = "continuation_action_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    departing_employee_id = Column(Integer, ForeignKey("employee_profiles.id", ondelete="CASCADE"), nullable=True, index=True)
    successor_id = Column(Integer, ForeignKey("employee_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    phase = Column(String(50), default="DAY_1", nullable=False)  # DAY_1, DAY_2_3, WEEK_1, DAY_30, DAY_60, DAY_90
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(50), default=PriorityLevel.HIGH.value, nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    relevant_files = Column(JSON, default=list)
    evidence_snippet = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="continuation_actions")
    departing_employee = relationship("EmployeeProfile", foreign_keys=[departing_employee_id])
    successor = relationship("EmployeeProfile", foreign_keys=[successor_id])

class ConflictItem(Base):
    __tablename__ = "conflict_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    statement_a = Column(Text, nullable=False)
    source_a = Column(String(255), nullable=False)
    statement_b = Column(Text, nullable=False)
    source_b = Column(String(255), nullable=False)
    conflict_type = Column(String(50), default="status_mismatch")  # status_mismatch, code_doc_conflict, ownership_conflict, unmerged_pr_vs_done
    resolution_status = Column(String(50), default="open")  # open, resolved
    resolved_by = Column(String(100), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="conflicts")

class SourceConnection(Base):
    __tablename__ = "source_connections"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # github, document_folder, jira, slack
    connection_name = Column(String(150), nullable=False)
    repository_url = Column(String(500), nullable=True)
    branch = Column(String(100), default="main")
    auth_token_preview = Column(String(50), nullable=True)
    sync_status = Column(String(50), default="connected")  # connected, syncing, synced, failed, synthetic_demo
    last_synced_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="source_connections")

