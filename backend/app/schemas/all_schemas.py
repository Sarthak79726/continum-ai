from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# --- AUTH & USER ---
class UserBase(BaseModel):
    name: str
    email: str

class UserRegister(UserBase):
    password: str = Field(min_length=6)
    role: Optional[str] = "TEAM_MEMBER"

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    refresh_token: Optional[str] = None

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class PasswordForgotRequest(BaseModel):
    email: str

class PasswordResetRequest(BaseModel):
    token: str
    new_password: str

class UserSessionResponse(BaseModel):
    id: int
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    is_revoked: bool
    created_at: datetime
    last_used_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}

# --- PROJECT & MEMBERSHIP ---
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[str] = "active"

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class ProjectMemberAdd(BaseModel):
    email: str
    role: str = "TEAM_MEMBER"

class ProjectMemberResponse(BaseModel):
    id: int
    user_id: int
    project_id: int
    name: str
    email: str
    role: str
    created_at: datetime

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    is_demo: bool
    created_at: datetime
    updated_at: datetime
    owner_name: Optional[str] = None
    document_count: Optional[int] = 0
    task_count: Optional[int] = 0
    risk_count: Optional[int] = 0

    model_config = {"from_attributes": True}

# --- DOCUMENT & CHUNKS ---
class DocumentResponse(BaseModel):
    id: int
    project_id: int
    uploaded_by: int
    filename: str
    file_type: str
    file_size: int
    processing_status: str
    error_message: Optional[str] = None
    chunk_count: Optional[int] = 0
    created_at: datetime

    model_config = {"from_attributes": True}

class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    extracted_text: str
    created_at: datetime

    model_config = {"from_attributes": True}

# --- EVIDENCE PASSPORT ---
class EvidenceResponse(BaseModel):
    id: int
    project_id: int
    document_id: int
    document_name: Optional[str] = None
    chunk_id: Optional[int] = None
    claim_text: str
    source_snippet: str
    page_number: Optional[int] = None
    verification_status: str  # VERIFIED, NEEDS_REVIEW, CONFLICTING, UNVERIFIED
    quality_label: str  # Direct Citation, Inferred, Conflicting, Insufficient Context
    created_at: datetime

    model_config = {"from_attributes": True}

class EvidenceVerifyRequest(BaseModel):
    verification_status: str
    quality_label: Optional[str] = None

# --- TASKS ---
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[str] = "pending"
    priority: Optional[str] = "medium"
    owner: Optional[str] = "Unassigned"
    due_date: Optional[str] = None
    source_reference: Optional[str] = None
    is_recommendation: Optional[bool] = False

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    owner: Optional[str] = None
    due_date: Optional[str] = None
    is_recommendation: Optional[bool] = None

class TaskResponse(TaskBase):
    id: int
    project_id: int
    evidence_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}

# --- DECISIONS ---
class DecisionCreate(BaseModel):
    title: str
    description: str
    reasoning: Optional[str] = None
    date_decided: Optional[str] = None
    source_reference: Optional[str] = None

class DecisionResponse(DecisionCreate):
    id: int
    project_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

# --- RISKS ---
class RiskCreate(BaseModel):
    title: str
    description: str
    severity: Optional[str] = "medium"
    status: Optional[str] = "active"
    impact: Optional[str] = None
    suggested_resolution: Optional[str] = None
    source_reference: Optional[str] = None

class RiskResponse(RiskCreate):
    id: int
    project_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

# --- DEPENDENCIES ---
class DependencyCreate(BaseModel):
    source_title: str
    target_title: str
    description: Optional[str] = None
    evidence: Optional[str] = None

class DependencyResponse(DependencyCreate):
    id: int
    project_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

# --- STRUCTURED KNOWLEDGE EXTRACTION SCHEMAS ---
class ExtractedOverview(BaseModel):
    project_purpose: str
    main_objectives: List[str] = []
    current_development_stage: str
    important_technical_components: List[str] = []
    evidence_snippet: Optional[str] = None
    source_document: Optional[str] = None

class ExtractedTaskItem(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"  # completed, in_progress, pending, blocked
    owner: Optional[str] = "Unknown"
    completion_evidence: Optional[str] = None
    source_document: Optional[str] = None
    page_number: Optional[int] = None
    verification_status: str = "NEEDS_REVIEW"

class ExtractedDecisionItem(BaseModel):
    title: str
    description: str
    reasoning: Optional[str] = None
    date_decided: Optional[str] = "Unknown"
    source_document: Optional[str] = None
    evidence_snippet: Optional[str] = None

class ExtractedRiskItem(BaseModel):
    title: str
    description: str
    severity: str = "medium"  # critical, high, medium, low
    potential_impact: Optional[str] = None
    suggested_resolution: Optional[str] = None
    source_document: Optional[str] = None
    evidence_snippet: Optional[str] = None

class ExtractedDependencyItem(BaseModel):
    source_title: str
    target_title: str
    dependency_explanation: Optional[str] = None
    evidence_snippet: Optional[str] = None
    source_document: Optional[str] = None

class ExtractedQuestionItem(BaseModel):
    question: str
    category: str  # missing_information, contradictory_information, unclear_ownership, unverified_claim
    details: str
    source_document: Optional[str] = None

class ProjectAnalysisPayload(BaseModel):
    overview: ExtractedOverview
    completed_tasks: List[ExtractedTaskItem] = []
    ongoing_tasks: List[ExtractedTaskItem] = []
    pending_tasks: List[ExtractedTaskItem] = []
    important_decisions: List[ExtractedDecisionItem] = []
    risks_and_blockers: List[ExtractedRiskItem] = []
    dependencies: List[ExtractedDependencyItem] = []
    unresolved_questions: List[ExtractedQuestionItem] = []
    recommended_next_actions: List[str] = []

# --- KNOWLEDGE GRAPH ---
class GraphNodeData(BaseModel):
    label: str
    type: str  # project, person, task, decision, risk, component, document
    status: Optional[str] = None
    priority: Optional[str] = None
    severity: Optional[str] = None
    evidence: Optional[str] = None
    source_document: Optional[str] = None
    details: Optional[str] = None

class GraphNode(BaseModel):
    id: str
    type: str
    data: GraphNodeData
    position: Dict[str, float]

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    animated: Optional[bool] = False
    style: Optional[Dict[str, Any]] = None

class KnowledgeGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

# --- HANDOVER REPORT & REVIEW ---
class HandoverCreate(BaseModel):
    title: Optional[str] = None
    view_mode: Optional[str] = "incoming_member_view"

class HandoverUpdate(BaseModel):
    title: Optional[str] = None
    report_content: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class ReviewCreate(BaseModel):
    action: str  # approved, rejected
    comments: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    report_id: int
    reviewer_id: int
    reviewer_name: Optional[str] = None
    action: str
    comments: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class HandoverResponse(BaseModel):
    id: int
    project_id: int
    project_name: Optional[str] = None
    created_by: int
    creator_name: Optional[str] = None
    title: str
    report_content: Dict[str, Any]
    status: str
    version: int
    view_mode: str
    created_at: datetime
    updated_at: datetime
    reviews: List[ReviewResponse] = []

    model_config = {"from_attributes": True}

# --- ANALYTICS & DASHBOARD ---
class DashboardStats(BaseModel):
    total_projects: int
    documents_processed: int
    completed_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    identified_risks: int
    handover_reports: int
    pending_reviews: int
    recent_projects: List[Dict[str, Any]] = []
    recent_documents: List[Dict[str, Any]] = []
    pending_review_reports: List[Dict[str, Any]] = []
    activity_timeline: List[Dict[str, Any]] = []
    task_completion_distribution: List[Dict[str, Any]] = []
    risk_severity_distribution: List[Dict[str, Any]] = []

# --- EMPLOYEE KNOWLEDGE PASSPORT & CODE INTELLIGENCE SCHEMAS ---

class EmployeeProfileBase(BaseModel):
    name: str
    employee_id_code: Optional[str] = None
    role_title: str
    department: Optional[str] = "Engineering"
    responsibilities: List[str] = []
    date_joined: Optional[str] = None
    handover_initiation_date: Optional[str] = None
    assigned_successor_id: Optional[int] = None
    handover_status: str = "ACTIVE"
    last_activity_date: Optional[str] = None
    contribution_summary: Optional[str] = None

class EmployeeProfileCreate(EmployeeProfileBase):
    project_id: int
    user_id: Optional[int] = None

class EmployeeProfileUpdate(BaseModel):
    name: Optional[str] = None
    employee_id_code: Optional[str] = None
    role_title: Optional[str] = None
    department: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    handover_initiation_date: Optional[str] = None
    assigned_successor_id: Optional[int] = None
    handover_status: Optional[str] = None
    last_activity_date: Optional[str] = None
    contribution_summary: Optional[str] = None

class EmployeeProfileResponse(EmployeeProfileBase):
    id: int
    project_id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    successor_name: Optional[str] = None

    model_config = {"from_attributes": True}

class CommitRecordResponse(BaseModel):
    id: int
    project_id: int
    employee_id: int
    commit_hash: str
    message: str
    branch: str
    changed_files: List[str] = []
    insertions: int = 0
    deletions: int = 0
    is_merged: bool = True
    has_tests: bool = False
    affected_modules: List[str] = []
    timestamp: Optional[str] = None
    source_url: Optional[str] = None

    model_config = {"from_attributes": True}

class PullRequestRecordResponse(BaseModel):
    id: int
    project_id: int
    employee_id: int
    pr_number: int
    title: str
    description: Optional[str] = None
    source_branch: str
    target_branch: str
    is_merged: bool = False
    has_tests: bool = False
    open_review_comments: int = 0
    review_notes: Optional[str] = None
    timestamp: Optional[str] = None
    source_url: Optional[str] = None

    model_config = {"from_attributes": True}

class APIEndpointRecordResponse(BaseModel):
    id: int
    project_id: int
    employee_id: Optional[int] = None
    method: str
    endpoint_path: str
    description: Optional[str] = None
    backend_module: str
    request_params: Dict[str, Any] = {}
    request_body: Dict[str, Any] = {}
    response_structure: Dict[str, Any] = {}
    auth_required: bool = True
    permissions_required: str = "Authenticated"
    database_tables: List[str] = []
    frontend_callers: List[str] = []
    test_coverage_status: str = "MISSING_TESTS"
    implementation_status: str = "COMPLETED"
    source_reference: Optional[str] = None
    last_modified: Optional[str] = None

    model_config = {"from_attributes": True}

class DatabaseSchemaRecordResponse(BaseModel):
    id: int
    project_id: int
    employee_id: Optional[int] = None
    model_name: str
    table_name: str
    description: Optional[str] = None
    columns: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    foreign_keys: List[Dict[str, Any]] = []
    indexes: List[str] = []
    migration_script: Optional[str] = None
    is_pending: bool = False
    dependent_modules: List[str] = []

    model_config = {"from_attributes": True}

class BugDebtItemResponse(BaseModel):
    id: int
    project_id: int
    employee_id: Optional[int] = None
    issue_code: str
    title: str
    description: str
    classification: str
    severity: str
    priority: str
    affected_module: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    evidence_snippet: Optional[str] = None
    investigation_performed: Optional[str] = None
    fixes_attempted: Optional[str] = None
    why_unresolved: Optional[str] = None
    recommended_next_action: Optional[str] = None
    confidence_level: str = "HIGH"
    created_at: datetime

    model_config = {"from_attributes": True}

class BlockerItemResponse(BaseModel):
    id: int
    project_id: int
    employee_id: Optional[int] = None
    title: str
    description: str
    failed_attempts: Optional[str] = None
    external_dependency: Optional[str] = None
    required_assistance: Optional[str] = None
    status: str = "active"
    created_at: datetime

    model_config = {"from_attributes": True}

class KnowledgeGapItemResponse(BaseModel):
    id: int
    project_id: int
    employee_id: Optional[int] = None
    title: str
    category: str
    description: str
    affected_component: Optional[str] = None
    severity: str = "medium"
    created_at: datetime

    model_config = {"from_attributes": True}

class WorkTimelineEventResponse(BaseModel):
    id: int
    project_id: int
    employee_id: int
    timestamp: str
    event_type: str
    title: str
    description: Optional[str] = None
    source_reference: Optional[str] = None
    verification_status: str = "VERIFIED"
    source_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class ContinuationActionItemResponse(BaseModel):
    id: int
    project_id: int
    departing_employee_id: Optional[int] = None
    successor_id: Optional[int] = None
    phase: str
    title: str
    description: Optional[str] = None
    priority: str
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    relevant_files: List[str] = []
    evidence_snippet: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class ConflictItemResponse(BaseModel):
    id: int
    project_id: int
    title: str
    statement_a: str
    source_a: str
    statement_b: str
    source_b: str
    conflict_type: str
    resolution_status: str
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class SourceConnectionResponse(BaseModel):
    id: int
    project_id: int
    source_type: str
    connection_name: str
    repository_url: Optional[str] = None
    branch: str = "main"
    auth_token_preview: Optional[str] = None
    sync_status: str = "connected"
    last_synced_at: Optional[datetime] = None
    metadata_json: Dict[str, Any] = {}
    created_at: datetime

    model_config = {"from_attributes": True}

class EmployeePassportResponse(BaseModel):
    employee: EmployeeProfileResponse
    successor: Optional[EmployeeProfileResponse] = None
    timeline: List[WorkTimelineEventResponse] = []
    commits: List[CommitRecordResponse] = []
    pull_requests: List[PullRequestRecordResponse] = []
    api_endpoints: List[APIEndpointRecordResponse] = []
    schema_records: List[DatabaseSchemaRecordResponse] = []
    bugs_and_debt: List[BugDebtItemResponse] = []
    blockers: List[BlockerItemResponse] = []
    knowledge_gaps: List[KnowledgeGapItemResponse] = []
    tasks: List[TaskResponse] = []
    decisions: List[DecisionResponse] = []
    continuation_plan: List[ContinuationActionItemResponse] = []

class HandoverInitiateRequest(BaseModel):
    departing_employee_id: int
    successor_id: Optional[int] = None
    notes: Optional[str] = None

class HandoverAcknowledgeRequest(BaseModel):
    comments: Optional[str] = None

class AskCitation(BaseModel):
    source_type: str  # document, commit, api, pull_request, task
    title: str
    reference: str  # URL, file path, commit hash, page number
    quote_snippet: Optional[str] = None

class AskProjectAIRequest(BaseModel):
    project_id: int
    question: str
    employee_id: Optional[int] = None
    role_scope: Optional[str] = "BACKEND"  # BACKEND, FRONTEND, ALL

class AskProjectAIResponse(BaseModel):
    answer: str
    confidence: str  # HIGH, MEDIUM, LOW, INSUFFICIENT_EVIDENCE
    citations: List[AskCitation] = []
    missing_evidence_notice: Optional[str] = None
    contradictions_noted: Optional[str] = None
    recommended_follow_ups: List[str] = []


