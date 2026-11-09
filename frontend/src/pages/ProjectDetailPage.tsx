import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FolderGit2,
  FileText,
  Sparkles,
  Upload,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Network,
  FileCheck2,
  Layers,
  ArrowRight,
  ShieldCheck,
  Plus,
  Trash2,
  Download,
  Eye,
  RefreshCw,
  GitFork,
  HelpCircle
} from 'lucide-react';
import {
  projectApi,
  documentApi,
  aiApi,
  taskApi,
  handoverApi,
  evidenceApi,
  graphApi
} from '../services/api';
import {
  Project,
  ProjectDocument,
  TaskItem,
  EvidenceItem,
  HandoverReport,
  KnowledgeGraphData,
  DocumentChunk
} from '../types';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { EmptyState } from '../components/common/EmptyState';

export const ProjectDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const navigate = useNavigate();

  const [project, setProject] = useState<Project | null>(null);
  const [activeTab, setActiveTab] = useState<
    'overview' | 'documents' | 'tasks' | 'decisions' | 'dependencies' | 'risks' | 'graph' | 'handovers'
  >('overview');

  // Tab Data States
  const [documents, setDocuments] = useState<ProjectDocument[]>([]);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [handovers, setHandovers] = useState<HandoverReport[]>([]);
  const [graphData, setGraphData] = useState<KnowledgeGraphData | null>(null);
  const [knowledgeData, setKnowledgeData] = useState<any>(null);

  // Status & Loaders
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeNotice, setAnalyzeNotice] = useState<string | null>(null);

  // Upload state
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Document chunk inspector modal
  const [inspectDoc, setInspectDoc] = useState<ProjectDocument | null>(null);
  const [docChunks, setDocChunks] = useState<DocumentChunk[]>([]);
  const [loadingChunks, setLoadingChunks] = useState(false);

  // Task creation modal
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDesc, setTaskDesc] = useState('');
  const [taskStatus, setTaskStatus] = useState<'pending' | 'in_progress' | 'completed' | 'blocked'>('pending');
  const [taskPriority, setTaskPriority] = useState<'critical' | 'high' | 'medium' | 'low'>('medium');
  const [taskOwner, setTaskOwner] = useState('Rahul');

  useEffect(() => {
    if (projectId) {
      loadProjectData();
    }
  }, [projectId]);

  const loadProjectData = async () => {
    try {
      setLoading(true);
      const [proj, docs, tList, evList, hList, kObj, gData] = await Promise.all([
        projectApi.get(projectId),
        documentApi.list(projectId),
        taskApi.list(projectId),
        evidenceApi.list(projectId),
        handoverApi.list(projectId),
        aiApi.getKnowledge(projectId).catch(() => ({ categories: {} })),
        graphApi.getGraph(projectId).catch(() => ({ nodes: [], edges: [] })),
      ]);

      setProject(proj);
      setDocuments(docs);
      setTasks(tList);
      setEvidenceList(evList);
      setHandovers(hList);
      setKnowledgeData(kObj.categories);
      setGraphData(gData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    try {
      setAnalyzing(true);
      setAnalyzeNotice('Retrieving chunks & reconstructing project knowledge...');
      await aiApi.analyseProject(projectId);
      setAnalyzeNotice('Reconstruction complete! Re-indexing telemetry...');
      await loadProjectData();
      setTimeout(() => setAnalyzeNotice(null), 4000);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Analysis failed. Ensure at least one processed document exists.');
      setAnalyzeNotice(null);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setUploadError(null);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      await documentApi.upload(projectId, formData);
      await loadProjectData();
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Failed to upload files.');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (docId: number) => {
    if (!window.confirm('Delete this document and remove its chunks from vector search?')) return;
    try {
      await documentApi.delete(docId);
      setDocuments(documents.filter((d) => d.id !== docId));
      await loadProjectData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleInspectChunks = async (doc: ProjectDocument) => {
    setInspectDoc(doc);
    setLoadingChunks(true);
    try {
      const chunks = await documentApi.getChunks(doc.id);
      setDocChunks(chunks);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingChunks(false);
    }
  };

  const handleDownloadDocument = async (doc: ProjectDocument) => {
    try {
      const blob = await documentApi.download(doc.id);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', doc.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed', err);
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskTitle.trim()) return;

    try {
      const created = await taskApi.create(projectId, {
        title: taskTitle,
        description: taskDesc,
        status: taskStatus,
        priority: taskPriority,
        owner: taskOwner,
        is_recommendation: false,
      });
      setTasks([...tasks, created]);
      setIsTaskModalOpen(false);
      setTaskTitle('');
      setTaskDesc('');
    } catch (err) {
      console.error(err);
    }
  };

  const handleTaskStatusChange = async (taskId: number, newStatus: TaskItem['status']) => {
    try {
      const updated = await taskApi.update(taskId, { status: newStatus });
      setTasks(tasks.map((t) => (t.id === taskId ? updated : t)));
    } catch (err) {
      console.error(err);
    }
  };

  const handleGenerateHandover = async (mode: 'incoming_member_view' | 'pm_view') => {
    try {
      setLoading(true);
      const res = await handoverApi.generate(projectId, {
        title: `Knowledge Handover — ${project?.name} (v${handovers.length + 1})`,
        view_mode: mode,
      });
      setHandovers([res, ...handovers]);
      setActiveTab('handovers');
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = async (reportId: number) => {
    try {
      const blob = await handoverApi.downloadPdf(reportId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Continuum_Handover_Project_${projectId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading && !project) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-xs text-slate-500 font-mono animate-pulse">
          Loading project knowledge graph & telemetry...
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <h2 className="text-base font-semibold text-slate-900">Project Not Found</h2>
        <button onClick={() => navigate('/projects')} className="mt-3 text-xs text-teal-600 underline">
          Return to Projects
        </button>
      </div>
    );
  }

  const overview = knowledgeData?.overview?.content;
  const decisions = knowledgeData?.important_decisions?.content || [];
  const risks = knowledgeData?.risks_and_blockers?.content || [];
  const dependencies = knowledgeData?.dependencies?.content || [];
  const questions = knowledgeData?.unresolved_questions?.content || [];

  return (
    <div className="space-y-6">
      {/* Project Banner & Action Bar */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">{project.name}</h1>
              {project.is_demo && <Badge variant="needs_review">DEMO DATA</Badge>}
              <Badge variant={project.status === 'active' ? 'completed' : 'default'}>
                {project.status.toUpperCase()}
              </Badge>
            </div>
            <p className="text-xs text-slate-500 max-w-3xl leading-relaxed">
              {project.description || 'Knowledge transition workspace.'}
            </p>
          </div>

          {/* Core Action: ANALYSE PROJECT */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={handleRunAnalysis}
              disabled={analyzing || documents.length === 0}
              className="px-4 py-2 text-xs font-semibold text-slate-950 bg-teal-400 hover:bg-teal-300 rounded-lg shadow-sm shadow-teal-500/20 flex items-center gap-1.5 transition-all disabled:opacity-50"
              title={documents.length === 0 ? 'Upload documents first' : 'Reconstruct project state'}
            >
              <Sparkles className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
              {analyzing ? 'Analysing Knowledge...' : 'ANALYSE PROJECT'}
            </button>
          </div>
        </div>

        {analyzeNotice && (
          <div className="mt-4 p-2.5 bg-teal-50 border border-teal-200 rounded-lg text-teal-800 text-xs flex items-center gap-2 animate-in fade-in">
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-teal-600" />
            <span>{analyzeNotice}</span>
          </div>
        )}
      </div>

      {/* 8 Project Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6 overflow-x-auto text-xs font-medium">
          {[
            { id: 'overview', label: '1. Overview' },
            { id: 'documents', label: `2. Documents (${documents.length})` },
            { id: 'tasks', label: `3. Tasks (${tasks.length})` },
            { id: 'decisions', label: `4. Decisions (${decisions.length})` },
            { id: 'dependencies', label: `5. Dependencies (${dependencies.length})` },
            { id: 'risks', label: `6. Risks (${risks.length})` },
            { id: 'graph', label: '7. Knowledge Graph' },
            { id: 'handovers', label: `8. Handovers (${handovers.length})` },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`pb-3 px-1 border-b-2 transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-teal-500 text-teal-600 font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-900 hover:border-slate-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2 space-y-6">
              {/* Purpose & Stage Card */}
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
                <div>
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-1">
                    System Purpose & Scope
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {overview?.project_purpose || project.description || 'Information awaiting AI reconstruction.'}
                  </p>
                </div>

                <div>
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-1">
                    Current Stage
                  </h3>
                  <Badge variant="in_progress">
                    {overview?.current_development_stage || 'Active Development & Handover'}
                  </Badge>
                </div>

                {overview?.main_objectives && overview.main_objectives.length > 0 && (
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-1.5">
                      Verified Objectives
                    </h3>
                    <ul className="space-y-1 text-xs text-slate-600">
                      {overview.main_objectives.map((obj: string, i: number) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0 mt-0.5" />
                          <span>{obj}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Technical Components */}
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3">
                  Architecture Components
                </h3>
                <div className="flex flex-wrap gap-2">
                  {(overview?.important_technical_components || [
                    'FastAPI Engine',
                    'React Frontend',
                    'Payment Integration Module',
                    'ChromaDB Vector Store',
                  ]).map((comp: string, i: number) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 bg-slate-100 text-slate-800 rounded-lg text-xs font-medium border border-slate-200"
                    >
                      {comp}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Quick Handover Readiness Sidebar */}
            <div className="space-y-6">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3">
                  Handover Readiness
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Documents Processed</span>
                    <span className="font-semibold text-slate-800">{documents.length}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Extracted Claims</span>
                    <span className="font-semibold text-slate-800">{evidenceList.length}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Tasks Reconstructed</span>
                    <span className="font-semibold text-slate-800">{tasks.length}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Identified Risks</span>
                    <span className="font-semibold text-rose-600">{risks.length}</span>
                  </div>
                </div>

                <div className="pt-4 mt-4 border-t border-slate-100">
                  <button
                    onClick={() => handleGenerateHandover('incoming_member_view')}
                    className="w-full py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-colors"
                  >
                    <FileCheck2 className="w-3.5 h-3.5" />
                    Generate Continuity Report
                  </button>
                </div>
              </div>

              {/* Unresolved Questions */}
              {questions.length > 0 && (
                <div className="bg-amber-50/60 p-5 rounded-xl border border-amber-200/80">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-amber-900 uppercase tracking-wider mb-2">
                    <HelpCircle className="w-4 h-4 text-amber-600" />
                    Unresolved Ambiguities ({questions.length})
                  </div>
                  <div className="space-y-2">
                    {questions.map((q: any, i: number) => (
                      <div key={i} className="text-[11px] text-amber-900/90 leading-tight">
                        • {q.question || q}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: DOCUMENTS */}
      {activeTab === 'documents' && (
        <div className="space-y-6">
          {/* Upload Drag & Drop Box */}
          <div className="bg-white p-6 rounded-xl border-2 border-dashed border-slate-200 hover:border-teal-500/60 transition-colors text-center">
            <input
              type="file"
              ref={fileInputRef}
              multiple
              accept=".pdf,.docx,.doc,.txt,.csv,.md"
              onChange={handleFileUpload}
              className="hidden"
              id="doc-upload"
            />
            <label htmlFor="doc-upload" className="cursor-pointer flex flex-col items-center">
              <div className="w-10 h-10 rounded-full bg-teal-50 flex items-center justify-center text-teal-600 mb-2 border border-teal-100">
                <Upload className="w-5 h-5" />
              </div>
              <span className="text-xs font-semibold text-slate-800">
                Click to upload or drag and drop project documentation
              </span>
              <span className="text-[11px] text-slate-500 mt-0.5">
                Supports PDF, DOCX, TXT, and CSV up to 20MB per file
              </span>
            </label>
            {uploading && (
              <div className="mt-3 text-xs text-teal-600 font-mono animate-pulse">
                Ingesting and generating ChromaDB embeddings...
              </div>
            )}
            {uploadError && (
              <div className="mt-3 text-xs text-rose-600">{uploadError}</div>
            )}
          </div>

          {/* Document Registry Table */}
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Ingested Project Documents ({documents.length})
              </h3>
              <span className="text-[11px] text-slate-500">Vector Index Ready</span>
            </div>

            {documents.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-400">
                No documents uploaded yet. Add PDF, DOCX, CSV or TXT files above.
              </div>
            ) : (
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-medium border-b border-slate-100">
                  <tr>
                    <th className="px-5 py-2.5">File Name</th>
                    <th className="px-4 py-2.5">Type</th>
                    <th className="px-4 py-2.5">Chunks</th>
                    <th className="px-4 py-2.5">Size</th>
                    <th className="px-4 py-2.5">Status</th>
                    <th className="px-4 py-2.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-slate-50/50">
                      <td className="px-5 py-3 font-medium text-slate-900 flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5 text-slate-400" />
                        <span>{doc.filename}</span>
                      </td>
                      <td className="px-4 py-3 uppercase text-slate-500 font-mono text-[10px]">
                        {doc.file_type}
                      </td>
                      <td className="px-4 py-3 text-slate-600">{doc.chunk_count} chunks</td>
                      <td className="px-4 py-3 text-slate-500">
                        {(doc.file_size / 1024).toFixed(1)} KB
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={
                            doc.processing_status === 'processed'
                              ? 'verified'
                              : doc.processing_status === 'failed'
                              ? 'conflicting'
                              : 'needs_review'
                          }
                        >
                          {doc.processing_status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleDownloadDocument(doc)}
                            className="p-1 text-slate-500 hover:text-teal-600 rounded hover:bg-slate-100"
                            title="Download Original Document"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleInspectChunks(doc)}
                            className="p-1 text-slate-500 hover:text-teal-600 rounded hover:bg-slate-100"
                            title="Inspect Chunks"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleDeleteDocument(doc.id)}
                            className="p-1 text-slate-500 hover:text-rose-600 rounded hover:bg-slate-100"
                            title="Delete Document"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: TASKS & CONTINUITY BLUEPRINT */}
      {activeTab === 'tasks' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Continuity Task Board ({tasks.length})
            </h3>
            <button
              onClick={() => setIsTaskModalOpen(true)}
              className="px-3 py-1.5 bg-slate-900 text-white rounded-lg text-xs font-semibold flex items-center gap-1 shadow-xs hover:bg-slate-800"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Task
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {['completed', 'in_progress', 'pending', 'blocked'].map((statusKey) => {
              const columnTasks = tasks.filter((t) => t.status === statusKey);
              const colTitles: Record<string, string> = {
                completed: 'Completed (Verified)',
                in_progress: 'In Progress',
                pending: 'Pending Continuation',
                blocked: 'Blocked & Needs Credentials',
              };

              return (
                <div key={statusKey} className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
                  <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
                    <span className="text-xs font-semibold text-slate-800">
                      {colTitles[statusKey]}
                    </span>
                    <span className="text-[11px] font-mono font-medium text-slate-400">
                      {columnTasks.length}
                    </span>
                  </div>

                  <div className="space-y-2.5">
                    {columnTasks.map((t) => (
                      <div
                        key={t.id}
                        className={`p-3 rounded-lg border text-xs transition-all ${
                          t.is_recommendation
                            ? 'border-teal-200 bg-teal-50/20'
                            : 'border-slate-200 bg-white'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-1 mb-1.5">
                          <span className="font-semibold text-slate-900 leading-tight">
                            {t.title}
                          </span>
                          <Badge variant={t.priority as any}>{t.priority}</Badge>
                        </div>

                        {t.description && (
                          <p className="text-[11px] text-slate-600 line-clamp-2 leading-relaxed mb-2">
                            {t.description}
                          </p>
                        )}

                        <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1.5 border-t border-slate-100">
                          <span className="font-medium text-slate-700">Owner: {t.owner}</span>
                          <select
                            value={t.status}
                            onChange={(e) => handleTaskStatusChange(t.id, e.target.value as any)}
                            className="bg-slate-50 border border-slate-200 rounded px-1.5 py-0.5 text-[10px] text-slate-700"
                          >
                            <option value="pending">Pending</option>
                            <option value="in_progress">In Progress</option>
                            <option value="completed">Completed</option>
                            <option value="blocked">Blocked</option>
                          </select>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 4: DECISIONS */}
      {activeTab === 'decisions' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-4">
              Recorded Architectural & Technical Decisions ({decisions.length})
            </h3>
            {decisions.length === 0 ? (
              <div className="text-xs text-slate-500 py-6 text-center">
                Click 'ANALYSE PROJECT' to extract decisions from meeting notes and documentation.
              </div>
            ) : (
              <div className="space-y-3">
                {decisions.map((d: any, idx: number) => (
                  <div key={idx} className="p-4 rounded-lg border border-slate-200 bg-slate-50/50">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="text-xs font-semibold text-slate-900">{d.title}</h4>
                      <span className="text-[11px] text-slate-500 font-mono">{d.date_decided}</span>
                    </div>
                    <p className="text-xs text-slate-600 mb-2 leading-relaxed">{d.description}</p>
                    {d.reasoning && (
                      <div className="text-[11px] text-teal-800 bg-teal-50/80 p-2 rounded border border-teal-100">
                        <span className="font-semibold">Reasoning:</span> {d.reasoning}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 5: DEPENDENCIES */}
      {activeTab === 'dependencies' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-4">
              Task & Component Dependencies ({dependencies.length})
            </h3>
            {dependencies.length === 0 ? (
              <div className="text-xs text-slate-500 py-6 text-center">
                No explicit dependencies detected.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {dependencies.map((dep: any, idx: number) => (
                  <div key={idx} className="p-3.5 rounded-lg border border-slate-200 bg-white flex items-center gap-3">
                    <GitFork className="w-5 h-5 text-teal-600 shrink-0" />
                    <div className="text-xs flex-1">
                      <div className="font-semibold text-slate-900">{dep.source_title}</div>
                      <div className="text-[11px] text-teal-700 flex items-center gap-1 my-0.5">
                        <ArrowRight className="w-3 h-3" /> depends on <span className="font-semibold">{dep.target_title}</span>
                      </div>
                      {dep.dependency_explanation && (
                        <div className="text-[11px] text-slate-500">{dep.dependency_explanation}</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 6: RISKS & BLOCKERS */}
      {activeTab === 'risks' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-4">
              Identified Risks & Blockers ({risks.length})
            </h3>
            <div className="space-y-3">
              {risks.map((r: any, idx: number) => (
                <div key={idx} className="p-4 rounded-lg border border-rose-200 bg-rose-50/20">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-rose-900">{r.title}</span>
                    <Badge variant={r.severity}>{r.severity.toUpperCase()}</Badge>
                  </div>
                  <p className="text-xs text-slate-700 mb-2 leading-relaxed">{r.description}</p>
                  {r.suggested_resolution && (
                    <div className="text-[11px] text-slate-600 bg-white p-2 rounded border border-rose-100">
                      <span className="font-semibold text-rose-800">Suggested Resolution:</span> {r.suggested_resolution}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 7: KNOWLEDGE GRAPH */}
      {activeTab === 'graph' && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Interactive Relationship Graph
              </h3>
              <p className="text-[11px] text-slate-500">
                Extracted node topology: People, components, tasks, decisions & blockers
              </p>
            </div>
            <button
              onClick={() => navigate('/graph')}
              className="text-xs text-teal-600 hover:text-teal-700 font-semibold flex items-center gap-1"
            >
              Open Fullscreen Studio <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="h-[460px] bg-slate-950 rounded-lg border border-slate-800 p-4 relative overflow-hidden flex flex-col justify-between">
            <div className="text-xs text-teal-400 font-mono flex items-center justify-between">
              <span>Nodes: {graphData?.nodes?.length || 0} | Edges: {graphData?.edges?.length || 0}</span>
              <span className="text-[10px] text-slate-400">Live Topological View</span>
            </div>

            {/* Visual SVG topology layout */}
            <div className="flex-1 flex items-center justify-center">
              <svg className="w-full h-full" viewBox="0 0 1000 500">
                {/* Render Edges */}
                {graphData?.edges.map((e, idx) => {
                  const sNode = graphData.nodes.find((n) => n.id === e.source);
                  const tNode = graphData.nodes.find((n) => n.id === e.target);
                  if (!sNode || !tNode) return null;
                  return (
                    <g key={idx}>
                      <line
                        x1={sNode.position.x}
                        y1={sNode.position.y}
                        x2={tNode.position.x}
                        y2={tNode.position.y}
                        stroke={e.style?.stroke || '#334155'}
                        strokeWidth={1.5}
                        strokeDasharray={e.animated ? '4 4' : undefined}
                      />
                    </g>
                  );
                })}

                {/* Render Nodes */}
                {graphData?.nodes.map((n) => {
                  const isRoot = n.type === 'project';
                  const isPerson = n.type === 'person';
                  const isRisk = n.type === 'risk';
                  const isComp = n.type === 'component';

                  let fill = '#1e293b';
                  let stroke = '#475569';
                  if (isRoot) { fill = '#0d9488'; stroke = '#2dd4bf'; }
                  else if (isPerson) { fill = '#0284c7'; stroke = '#38bdf8'; }
                  else if (isRisk) { fill = '#e11d48'; stroke = '#fb7185'; }
                  else if (isComp) { fill = '#4f46e5'; stroke = '#818cf8'; }

                  return (
                    <g key={n.id} className="cursor-pointer">
                      <circle
                        cx={n.position.x}
                        cy={n.position.y}
                        r={isRoot ? 28 : 20}
                        fill={fill}
                        stroke={stroke}
                        strokeWidth={2}
                      />
                      <text
                        x={n.position.x}
                        y={n.position.y + 30}
                        textAnchor="middle"
                        fill="#cbd5e1"
                        fontSize={10}
                        fontWeight="600"
                      >
                        {n.data.label.length > 22 ? n.data.label.slice(0, 20) + '...' : n.data.label}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>

            <div className="flex items-center justify-center gap-4 text-[10px] text-slate-400 border-t border-slate-800 pt-2">
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-teal-500" /> Project Root</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-sky-500" /> Key Person (Rahul)</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-indigo-500" /> Components</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-rose-500" /> Risks / Blockers</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-slate-500" /> Tasks</span>
            </div>
          </div>
        </div>
      )}

      {/* TAB 8: HANDOVERS */}
      {activeTab === 'handovers' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Handover Dossiers & Transition Plans ({handovers.length})
            </h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleGenerateHandover('incoming_member_view')}
                className="px-3 py-1.5 bg-slate-900 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 hover:bg-slate-800 shadow-xs"
              >
                <Plus className="w-3.5 h-3.5" />
                Generate Incoming Member View
              </button>
              <button
                onClick={() => handleGenerateHandover('pm_view')}
                className="px-3 py-1.5 bg-white border border-slate-300 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 hover:bg-slate-50 shadow-xs"
              >
                PM Audit View
              </button>
            </div>
          </div>

          <div className="space-y-3">
            {handovers.map((h) => (
              <div
                key={h.id}
                className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="text-xs font-bold text-slate-900">{h.title}</h4>
                    <Badge variant={h.status as any}>{h.status.toUpperCase()}</Badge>
                    <span className="text-[10px] text-slate-400 font-mono">v{h.version}</span>
                  </div>
                  <div className="text-[11px] text-slate-500 flex items-center gap-3">
                    <span>Generated by {h.creator_name}</span>
                    <span>•</span>
                    <span>Mode: {h.view_mode.replace('_', ' ').toUpperCase()}</span>
                    <span>•</span>
                    <span>{new Date(h.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleDownloadPdf(h.id)}
                    className="px-3 py-1.5 bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Export PDF
                  </button>
                  <button
                    onClick={() => navigate('/handovers')}
                    className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors"
                  >
                    Inspect 14 Sections <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chunks Inspector Modal */}
      <Modal
        isOpen={!!inspectDoc}
        onClose={() => setInspectDoc(null)}
        title={`Extracted Chunks: ${inspectDoc?.filename || ''}`}
        maxWidth="2xl"
      >
        {loadingChunks ? (
          <div className="text-center py-8 text-xs text-slate-500 font-mono animate-pulse">
            Fetching chunk embeddings from ChromaDB...
          </div>
        ) : (
          <div className="space-y-3">
            {docChunks.map((c) => (
              <div key={c.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1.5 font-mono">
                  <span>Chunk Index #{c.chunk_index}</span>
                  <span>Page {c.page_number || 1}</span>
                </div>
                <p className="text-slate-800 leading-relaxed font-mono text-[11px]">
                  {c.extracted_text}
                </p>
              </div>
            ))}
          </div>
        )}
      </Modal>

      {/* Task Creation Modal */}
      <Modal
        isOpen={isTaskModalOpen}
        onClose={() => setIsTaskModalOpen(false)}
        title="Add Project Continuity Task"
      >
        <form onSubmit={handleCreateTask} className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Task Title *</label>
            <input
              type="text"
              required
              value={taskTitle}
              onChange={(e) => setTaskTitle(e.target.value)}
              placeholder="e.g. Complete payment gateway webhook verification"
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Description</label>
            <textarea
              rows={2}
              value={taskDesc}
              onChange={(e) => setTaskDesc(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
            />
          </div>
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Status</label>
              <select
                value={taskStatus}
                onChange={(e) => setTaskStatus(e.target.value as any)}
                className="w-full px-2 py-1.5 text-xs border border-slate-300 rounded-lg"
              >
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="blocked">Blocked</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Priority</label>
              <select
                value={taskPriority}
                onChange={(e) => setTaskPriority(e.target.value as any)}
                className="w-full px-2 py-1.5 text-xs border border-slate-300 rounded-lg"
              >
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Owner</label>
              <input
                type="text"
                value={taskOwner}
                onChange={(e) => setTaskOwner(e.target.value)}
                className="w-full px-2 py-1.5 text-xs border border-slate-300 rounded-lg"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-3">
            <button
              type="button"
              onClick={() => setIsTaskModalOpen(false)}
              className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-1.5 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg"
            >
              Save Task
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

