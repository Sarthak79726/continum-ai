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
    token_type: str
    user: UserResponse

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None

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

