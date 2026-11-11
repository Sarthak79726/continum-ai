export type UserRole = 'ADMIN' | 'PROJECT_MANAGER' | 'TEAM_MEMBER' | 'INCOMING_MEMBER';

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Project {
  id: number;
  name: string;
  description: string | null;
  status: string;
  owner_id: number;
  owner_name: string;
  is_demo: boolean;
  document_count: number;
  task_count: number;
  risk_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectDocument {
  id: number;
  project_id: number;
  uploaded_by: number;
  filename: string;
  file_type: string;
  file_size: number;
  processing_status: 'uploaded' | 'processing' | 'processed' | 'failed';
  error_message: string | null;
  chunk_count: number;
  created_at: string;
}

export interface DocumentChunk {
  id: number;
  document_id: number;
  chunk_index: number;
  page_number: number | null;
  section_title: string | null;
  extracted_text: string;
  created_at: string;
}

export interface EvidenceItem {
  id: number;
  project_id: number;
  document_id: number;
  document_name: string;
  chunk_id: number | null;
  claim_text: string;
  source_snippet: string;
  page_number: number | null;
  verification_status: 'VERIFIED' | 'NEEDS_REVIEW' | 'CONFLICTING' | 'UNVERIFIED';
  quality_label: string;
  created_at: string;
}

export interface TaskItem {
  id: number;
  project_id: number;
  title: string;
  description: string | null;
  status: 'completed' | 'in_progress' | 'pending' | 'blocked';
  priority: 'critical' | 'high' | 'medium' | 'low';
  owner: string;
  due_date: string | null;
  source_reference: string | null;
  evidence_id: number | null;
  is_recommendation: boolean;
  created_at: string;
}

export interface DecisionItem {
  id: number;
  project_id: number;
  title: string;
  description: string;
  reasoning: string | null;
  date_decided: string | null;
  source_reference: string | null;
  created_at: string;
}

export interface RiskItem {
  id: number;
  project_id: number;
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  status: string;
  impact: string | null;
  suggested_resolution: string | null;
  source_reference: string | null;
  created_at: string;
}

export interface DependencyItem {
  id: number;
  project_id: number;
  source_title: string;
  target_title: string;
  description: string | null;
  evidence: string | null;
  created_at: string;
}

export interface ReviewItem {
  id: number;
  report_id: number;
  reviewer_id: number;
  reviewer_name: string;
  action: string;
  comments: string | null;
  created_at: string;
}

export interface HandoverReport {
  id: number;
  project_id: number;
  project_name: string;
  created_by: number;
  creator_name: string;
  title: string;
  report_content: Record<string, any>;
  status: 'draft' | 'pending_review' | 'approved' | 'rejected';
  version: number;
  view_mode: 'pm_view' | 'incoming_member_view';
  created_at: string;
  updated_at: string;
  reviews: ReviewItem[];
}

export interface GraphNode {
  id: string;
  type: string;
  data: {
    label: string;
    type: string;
    status?: string;
    priority?: string;
    severity?: string;
    evidence?: string;
    details?: string;
  };
  position: { x: number; y: number };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  animated?: boolean;
  style?: Record<string, any>;
}

export interface KnowledgeGraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface DashboardStats {
  total_projects: number;
  documents_processed: number;
  completed_tasks: number;
  pending_tasks: number;
  in_progress_tasks: number;
  identified_risks: number;
  handover_reports: number;
  pending_reviews: number;
  recent_projects: any[];
  recent_documents: any[];
  pending_review_reports: any[];
  activity_timeline: any[];
  task_completion_distribution: { name: string; value: number; color: string }[];
  risk_severity_distribution: { severity: string; count: number }[];
}

export interface ProjectMember {
  id: number;
  user_id: number;
  project_id: number;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

// --- EMPLOYEE KNOWLEDGE PASSPORT & CODE INTELLIGENCE ---

export interface EmployeeProfile {
  id: number;
  project_id: number;
  user_id: number | null;
  name: string;
  employee_id_code: string | null;
  role_title: string;
  department: string;
  responsibilities: string[];
  date_joined: string | null;
  handover_initiation_date: string | null;
  assigned_successor_id: number | null;
  successor_name?: string | null;
  handover_status: 'ACTIVE' | 'HANDOVER_INITIATED' | 'ANALYSING' | 'EVIDENCE_REVIEW' | 'PENDING_APPROVAL' | 'APPROVED' | 'SHARED' | 'ACKNOWLEDGED' | 'COMPLETED';
  last_activity_date: string | null;
  contribution_summary: string | null;
  created_at: string;
  updated_at: string;
}

export interface CommitRecord {
  id: number;
  project_id: number;
  employee_id: number;
  commit_hash: string;
  message: string;
  branch: string;
  changed_files: string[];
  insertions: number;
  deletions: number;
  is_merged: boolean;
  has_tests: boolean;
  affected_modules: string[];
  timestamp: string | null;
  source_url: string | null;
}

export interface PullRequestRecord {
  id: number;
  project_id: number;
  employee_id: number;
  pr_number: number;
  title: string;
  description: string | null;
  source_branch: string;
  target_branch: string;
  is_merged: boolean;
  has_tests: boolean;
  open_review_comments: number;
  review_notes: string | null;
  timestamp: string | null;
  source_url: string | null;
}

export interface APIEndpointRecord {
  id: number;
  project_id: number;
  employee_id: number | null;
  method: string;
  endpoint_path: string;
  description: string | null;
  backend_module: string;
  request_params: Record<string, any>;
  request_body: Record<string, any>;
  response_structure: Record<string, any>;
  auth_required: boolean;
  permissions_required: string;
  database_tables: string[];
  frontend_callers: string[];
  test_coverage_status: 'COVERED' | 'MISSING_TESTS' | 'PARTIALLY_TESTED';
  implementation_status: 'COMPLETED' | 'PARTIALLY_IMPLEMENTED' | 'NOT_IMPLEMENTED' | 'NEEDS_TESTING';
  source_reference: string | null;
  last_modified: string | null;
}

export interface DatabaseSchemaRecord {
  id: number;
  project_id: number;
  employee_id: number | null;
  model_name: string;
  table_name: string;
  description: string | null;
  columns: { name: string; type: string; nullable?: boolean; primary_key?: boolean; foreign_key?: string }[];
  relationships: { target: string; type: string }[];
  foreign_keys: string[];
  indexes: string[];
  migration_script: string | null;
  is_pending: boolean;
  dependent_modules: string[];
}

export interface BugDebtItem {
  id: number;
  project_id: number;
  employee_id: number | null;
  issue_code: string;
  title: string;
  description: string;
  classification: 'CONFIRMED UNRESOLVED' | 'POTENTIAL BUG' | 'NEEDS INVESTIGATION' | 'RESOLVED' | 'UNVERIFIED';
  severity: 'critical' | 'high' | 'medium' | 'low';
  priority: 'critical' | 'high' | 'medium' | 'low';
  affected_module: string;
  file_path: string | null;
  line_number: number | null;
  evidence_snippet: string | null;
  investigation_performed: string | null;
  fixes_attempted: string | null;
  why_unresolved: string | null;
  recommended_next_action: string | null;
  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW';
  created_at: string;
}

export interface BlockerItem {
  id: number;
  project_id: number;
  employee_id: number | null;
  title: string;
  description: string;
  failed_attempts: string | null;
  external_dependency: string | null;
  required_assistance: string | null;
  status: 'active' | 'resolved';
  created_at: string;
}

export interface KnowledgeGapItem {
  id: number;
  project_id: number;
  employee_id: number | null;
  title: string;
  category: string;
  description: string;
  affected_component: string | null;
  severity: string;
  created_at: string;
}

export interface WorkTimelineEvent {
  id: number;
  project_id: number;
  employee_id: number;
  timestamp: string;
  event_type: string;
  title: string;
  description: string | null;
  source_reference: string | null;
  verification_status: 'VERIFIED' | 'PARTIALLY_VERIFIED' | 'UNVERIFIED';
  source_url: string | null;
  created_at: string;
}

export interface ContinuationActionItem {
  id: number;
  project_id: number;
  departing_employee_id: number | null;
  successor_id: number | null;
  phase: 'DAY_1' | 'DAY_2_3' | 'WEEK_1' | 'DAY_30' | 'DAY_60' | 'DAY_90';
  title: string;
  description: string | null;
  priority: 'critical' | 'high' | 'medium';
  is_completed: boolean;
  completed_at: string | null;
  notes: string | null;
  relevant_files: string[];
  evidence_snippet: string | null;
  created_at: string;
}

export interface ConflictItem {
  id: number;
  project_id: number;
  title: string;
  statement_a: string;
  source_a: string;
  statement_b: string;
  source_b: string;
  conflict_type: string;
  resolution_status: 'open' | 'resolved';
  resolved_by: string | null;
  resolution_notes: string | null;
  created_at: string;
}

export interface SourceConnection {
  id: number;
  project_id: number;
  source_type: string;
  connection_name: string;
  repository_url: string | null;
  branch: string;
  auth_token_preview: string | null;
  sync_status: 'connected' | 'syncing' | 'synced' | 'failed' | 'synthetic_demo';
  last_synced_at: string | null;
  metadata_json: Record<string, any>;
  created_at: string;
}

export interface EmployeePassportData {
  employee: EmployeeProfile;
  successor: EmployeeProfile | null;
  timeline: WorkTimelineEvent[];
  commits: CommitRecord[];
  pull_requests: PullRequestRecord[];
  api_endpoints: APIEndpointRecord[];
  schema_records: DatabaseSchemaRecord[];
  bugs_and_debt: BugDebtItem[];
  blockers: BlockerItem[];
  knowledge_gaps: KnowledgeGapItem[];
  tasks: TaskItem[];
  decisions: DecisionItem[];
  continuation_plan: ContinuationActionItem[];
}

export interface AskCitation {
  source_type: string;
  title: string;
  reference: string;
  quote_snippet?: string | null;
}

export interface AskAIResponse {
  answer: string;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW' | 'INSUFFICIENT_EVIDENCE';
  citations: AskCitation[];
  missing_evidence_notice?: string | null;
  contradictions_noted?: string | null;
  recommended_follow_ups: string[];
}


