import axios from 'axios';
import {
  AuthResponse,
  Project,
  ProjectDocument,
  DocumentChunk,
  EvidenceItem,
  TaskItem,
  DecisionItem,
  RiskItem,
  DependencyItem,
  HandoverReport,
  KnowledgeGraphData,
  DashboardStats,
  ProjectMember,
  User,
  EmployeeProfile,
  EmployeePassportData,
  ContinuationActionItem,
  SourceConnection,
  ConflictItem,
  AskAIResponse
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('continuum_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for token expiry handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('continuum_token');
      localStorage.removeItem('continuum_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (data: { email: string; password: string }) =>
    api.post<AuthResponse>('/auth/login', data).then((res) => res.data),
  register: (data: { name: string; email: string; password: string; role?: string }) =>
    api.post<AuthResponse>('/auth/register', data).then((res) => res.data),
  getCurrentUser: () =>
    api.get<User>('/auth/me').then((res) => res.data),
};

export const projectApi = {
  list: () => api.get<Project[]>('/projects').then((res) => res.data),
  get: (id: number) => api.get<Project>(`/projects/${id}`).then((res) => res.data),
  create: (data: { name: string; description?: string; status?: string }) =>
    api.post<Project>('/projects', data).then((res) => res.data),
  update: (id: number, data: Partial<Project>) =>
    api.put<Project>(`/projects/${id}`, data).then((res) => res.data),
  delete: (id: number) => api.delete(`/projects/${id}`).then((res) => res.data),
  getAuditLogs: (projectId: number) =>
    api.get<any[]>(`/projects/${projectId}/audit-logs`).then((res) => res.data),
};

export const documentApi = {
  list: (projectId: number) =>
    api.get<ProjectDocument[]>(`/projects/${projectId}/documents`).then((res) => res.data),
  get: (id: number) =>
    api.get<ProjectDocument>(`/documents/${id}`).then((res) => res.data),
  getChunks: (id: number) =>
    api.get<DocumentChunk[]>(`/documents/${id}/chunks`).then((res) => res.data),
  upload: (projectId: number, formData: FormData) =>
    api.post<ProjectDocument[]>(`/projects/${projectId}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((res) => res.data),
  download: (id: number) =>
    api.get(`/documents/${id}/download`, { responseType: 'blob' }).then((res) => res.data),
  delete: (id: number) =>
    api.delete(`/documents/${id}`).then((res) => res.data),
};

export const aiApi = {
  analyseProject: (projectId: number) =>
    api.post<{ status: string; message: string; analysis: any }>(`/projects/${projectId}/analyse`).then((res) => res.data),
  getKnowledge: (projectId: number) =>
    api.get<{ project_id: number; categories: Record<string, any> }>(`/projects/${projectId}/knowledge`).then((res) => res.data),
};

export const evidenceApi = {
  list: (projectId: number) =>
    api.get<EvidenceItem[]>(`/projects/${projectId}/evidence`).then((res) => res.data),
  updateStatus: (evidenceId: number, data: { verification_status: string; quality_label?: string }) =>
    api.put<EvidenceItem>(`/evidence/${evidenceId}`, data).then((res) => res.data),
};

export const taskApi = {
  list: (projectId: number) =>
    api.get<TaskItem[]>(`/projects/${projectId}/tasks`).then((res) => res.data),
  create: (projectId: number, data: Partial<TaskItem>) =>
    api.post<TaskItem>(`/projects/${projectId}/tasks`, data).then((res) => res.data),
  update: (taskId: number, data: Partial<TaskItem>) =>
    api.put<TaskItem>(`/tasks/${taskId}`, data).then((res) => res.data),
  delete: (taskId: number) =>
    api.delete(`/tasks/${taskId}`).then((res) => res.data),
};

export const graphApi = {
  getGraph: (projectId: number) =>
    api.get<KnowledgeGraphData>(`/projects/${projectId}/graph`).then((res) => res.data),
};

export const handoverApi = {
  list: (projectId: number) =>
    api.get<HandoverReport[]>(`/projects/${projectId}/handovers`).then((res) => res.data),
  get: (reportId: number) =>
    api.get<HandoverReport>(`/handovers/${reportId}`).then((res) => res.data),
  generate: (projectId: number, data: { title?: string; view_mode?: string }) =>
    api.post<HandoverReport>(`/projects/${projectId}/handovers`, data).then((res) => res.data),
  update: (reportId: number, data: Partial<HandoverReport>) =>
    api.put<HandoverReport>(`/handovers/${reportId}`, data).then((res) => res.data),
  approve: (reportId: number, comments?: string) =>
    api.post<HandoverReport>(`/handovers/${reportId}/approve`, { action: 'approved', comments }).then((res) => res.data),
  reject: (reportId: number, comments?: string) =>
    api.post<HandoverReport>(`/handovers/${reportId}/reject`, { action: 'rejected', comments }).then((res) => res.data),
  downloadPdf: (reportId: number) =>
    api.get(`/handovers/${reportId}/pdf`, { responseType: 'blob' }).then((res) => res.data),
};

export const reviewApi = {
  listReviews: () =>
    api.get<{ pending: HandoverReport[]; approved: HandoverReport[]; rejected: HandoverReport[]; total_reviews: number }>('/reviews').then((res) => res.data),
};

export const teamApi = {
  listMembers: (projectId: number) =>
    api.get<ProjectMember[]>(`/projects/${projectId}/members`).then((res) => res.data),
  addMember: (projectId: number, data: { email: string; role: string }) =>
    api.post<ProjectMember>(`/projects/${projectId}/members`, data).then((res) => res.data),
  removeMember: (projectId: number, userId: number) =>
    api.delete(`/projects/${projectId}/members/${userId}`).then((res) => res.data),
};

export const analyticsApi = {
  getStats: () =>
    api.get<DashboardStats>('/analytics').then((res) => res.data),
};

export const demoApi = {
  loadDemo: () =>
    api.post<{ status: string; message: string; project_id: number; project_name: string }>('/demo/load').then((res) => res.data),
  purgeDemo: () =>
    api.delete<{ status: string; message: string }>('/demo/purge').then((res) => res.data),
};

export const settingsApi = {
  getStatus: () =>
    api.get<any>('/settings/status').then((res) => res.data),
  update: (data: { ai_provider?: string; ai_api_key?: string; ai_model?: string }) =>
    api.put<any>('/settings', data).then((res) => res.data),
};

export const employeeApi = {
  listByProject: (projectId: number) =>
    api.get<EmployeeProfile[]>(`/employees/project/${projectId}`).then((res) => res.data),
  get: (id: number) =>
    api.get<EmployeeProfile>(`/employees/${id}`).then((res) => res.data),
  create: (projectId: number, data: Partial<EmployeeProfile>) =>
    api.post<EmployeeProfile>(`/employees/project/${projectId}`, data).then((res) => res.data),
  update: (id: number, data: Partial<EmployeeProfile>) =>
    api.put<EmployeeProfile>(`/employees/${id}`, data).then((res) => res.data),
  getPassport: (id: number) =>
    api.get<EmployeePassportData>(`/employees/${id}/passport`).then((res) => res.data),
  reconstruct: (id: number) =>
    api.post<EmployeePassportData>(`/employees/${id}/reconstruct`).then((res) => res.data),
  initiateHandover: (id: number, data: { successor_id?: number; notes?: string }) =>
    api.post<{ status: string; message: string; data: any }>(`/employees/${id}/handover/initiate`, data).then((res) => res.data),
  acknowledgeHandover: (id: number, data: { comments?: string }) =>
    api.post<{ status: string; message: string; acknowledged_at: string; acknowledged_by: string }>(`/employees/${id}/handover/acknowledge`, data).then((res) => res.data),
  getActions: (id: number) =>
    api.get<ContinuationActionItem[]>(`/employees/${id}/actions`).then((res) => res.data),
  toggleAction: (actionId: number) =>
    api.put<ContinuationActionItem>(`/employees/actions/${actionId}/toggle`).then((res) => res.data),
};

export const sourceApi = {
  listByProject: (projectId: number) =>
    api.get<SourceConnection[]>(`/sources/project/${projectId}`).then((res) => res.data),
  connectGitHub: (projectId: number, data: { owner: string; repo: string; branch?: string; token?: string }) =>
    api.post<any>(`/sources/project/${projectId}/github/connect`, data).then((res) => res.data),
  syncGitHub: (projectId: number) =>
    api.post<any>(`/sources/project/${projectId}/github/sync`).then((res) => res.data),
};

export const conflictApi = {
  listByProject: (projectId: number) =>
    api.get<ConflictItem[]>(`/conflicts/project/${projectId}`).then((res) => res.data),
  resolve: (conflictId: number, data: { resolution_notes: string }) =>
    api.post<ConflictItem>(`/conflicts/${conflictId}/resolve`, data).then((res) => res.data),
};

export const askAiApi = {
  ask: (data: { project_id: number; question: string; employee_id?: number; role_scope?: string }) =>
    api.post<AskAIResponse>('/ai/ask', data).then((res) => res.data),
};

export default api;

