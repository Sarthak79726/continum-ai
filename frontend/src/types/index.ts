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

