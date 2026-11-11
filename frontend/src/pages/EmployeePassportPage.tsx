import React, { useState, useEffect } from 'react';
import {
  UserCheck,
  GitCommit,
  GitPullRequest,
  Code2,
  Database,
  Bug,
  AlertTriangle,
  Clock,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  Search,
  Filter,
  CheckSquare,
  Square,
  FileText,
  UserPlus
} from 'lucide-react';
import {
  projectApi,
  employeeApi
} from '../services/api';
import {
  Project,
  EmployeeProfile,
  EmployeePassportData,
  ContinuationActionItem,
  APIEndpointRecord,
  BugDebtItem,
  WorkTimelineEvent
} from '../types';

export const EmployeePassportPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [employees, setEmployees] = useState<EmployeeProfile[]>([]);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null);
  const [passportData, setPassportData] = useState<EmployeePassportData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isReconstructing, setIsReconstructing] = useState(false);
  const [activeTab, setActiveTab] = useState<
    'overview' | 'timeline' | 'code' | 'apis' | 'database' | 'bugs' | 'blockers' | 'checklist'
  >('overview');

  // Modal for Handover Initiation
  const [showInitiateModal, setShowInitiateModal] = useState(false);
  const [successorId, setSuccessorId] = useState<number | ''>('');
  const [handoverNotes, setHandoverNotes] = useState('');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Load Projects on Mount
  useEffect(() => {
    projectApi.list().then((projs) => {
      setProjects(projs);
      if (projs.length > 0) {
        setSelectedProjectId(projs[0].id);
      }
    }).catch(console.error);
  }, []);

  // Load Employees when Project changes
  useEffect(() => {
    if (!selectedProjectId) return;
    employeeApi.listByProject(selectedProjectId).then((emps) => {
      setEmployees(emps);
      if (emps.length > 0) {
        // Prefer Rahul or first employee
        const rahul = emps.find((e) => e.name.toLowerCase().includes('rahul'));
        setSelectedEmployeeId(rahul ? rahul.id : emps[0].id);
      } else {
        setSelectedEmployeeId(null);
        setPassportData(null);
      }
    }).catch(console.error);
  }, [selectedProjectId]);

  // Load Full Passport when Employee changes
  useEffect(() => {
    if (!selectedEmployeeId) {
      setPassportData(null);
      return;
    }
    loadPassport(selectedEmployeeId);
  }, [selectedEmployeeId]);

  const loadPassport = async (empId: number) => {
    try {
      setIsLoading(true);
      const data = await employeeApi.getPassport(empId);
      setPassportData(data);
    } catch (err) {
      console.error('Failed to load employee passport:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReconstruct = async () => {
    if (!selectedEmployeeId) return;
    try {
      setIsReconstructing(true);
      const data = await employeeApi.reconstruct(selectedEmployeeId);
      setPassportData(data);
      setStatusMessage('Knowledge Passport reconstructed from authorized repository and document sources!');
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err) {
      console.error(err);
      setStatusMessage('Reconstruction failed.');
    } finally {
      setIsReconstructing(false);
    }
  };

  const handleInitiateHandover = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEmployeeId) return;
    try {
      await employeeApi.initiateHandover(selectedEmployeeId, {
        successor_id: successorId ? Number(successorId) : undefined,
        notes: handoverNotes
      });
      setShowInitiateModal(false);
      setStatusMessage('Handover initiated successfully!');
      loadPassport(selectedEmployeeId);
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err) {
      console.error(err);
      setStatusMessage('Failed to initiate handover.');
    }
  };

  const handleToggleChecklist = async (actionId: number) => {
    try {
      const updated = await employeeApi.toggleAction(actionId);
      if (passportData) {
        setPassportData({
          ...passportData,
          continuation_plan: passportData.continuation_plan.map((item) =>
            item.id === actionId ? updated : item
          )
        });
      }
    } catch (err) {
      console.error('Failed to toggle checklist item:', err);
    }
  };

  const activeEmployee = passportData?.employee;

  return (
    <div className="space-y-6">
      {/* Page Title & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-500/10 text-teal-400 border border-teal-500/30">
              Continuity Intelligence
            </span>
            <span className="text-xs text-slate-400 font-mono">ISO/IEC 27001 Evidence Grounded</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-1 flex items-center gap-2">
            <UserCheck className="w-7 h-7 text-teal-400" />
            Employee Knowledge Passport
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Authoritative institutional memory passport reconstructing what departing engineers built, decided, left incomplete, and blocked.
          </p>
        </div>

        {/* Project Selector */}
        <div className="flex items-center gap-3">
          <label className="text-xs font-medium text-slate-400">Project:</label>
          <select
            value={selectedProjectId || ''}
            onChange={(e) => setSelectedProjectId(Number(e.target.value))}
            className="bg-slate-800 text-slate-200 text-xs px-3 py-2 rounded-lg border border-slate-700 focus:outline-hidden focus:border-teal-500"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {statusMessage && (
        <div className="p-3 bg-teal-500/10 border border-teal-500/40 rounded-xl text-teal-300 text-xs flex items-center justify-between animate-fadeIn">
          <span>{statusMessage}</span>
          <button onClick={() => setStatusMessage(null)} className="text-teal-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Employee Selector Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {employees.map((emp) => {
          const isSelected = emp.id === selectedEmployeeId;
          const isDeparting = emp.handover_status.includes('IN_PROGRESS') || emp.handover_status.includes('INITIATED');
          return (
            <button
              key={emp.id}
              onClick={() => setSelectedEmployeeId(emp.id)}
              className={`text-left p-3.5 rounded-xl border transition-all ${
                isSelected
                  ? 'bg-slate-800 border-teal-500/50 shadow-md shadow-teal-500/10'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/40'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center font-bold text-xs text-white">
                  {emp.name.split(' ').map((n) => n[0]).join('')}
                </div>
                <span
                  className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                    isDeparting
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : emp.handover_status.includes('COMPLETED')
                      ? 'bg-teal-500/20 text-teal-300 border border-teal-500/30'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {emp.handover_status.replace(/_/g, ' ')}
                </span>
              </div>
              <div className="mt-2.5">
                <div className="text-xs font-semibold text-white">{emp.name}</div>
                <div className="text-[11px] text-slate-400 truncate">{emp.role_title}</div>
                <div className="text-[10px] text-slate-500 font-mono mt-0.5">{emp.employee_id_code}</div>
              </div>
            </button>
          );
        })}
      </div>

      {isLoading ? (
        <div className="p-16 text-center text-slate-400">
          <div className="inline-block w-6 h-6 border-2 border-teal-500 border-t-transparent rounded-full animate-spin mb-2" />
          <p className="text-xs">Reconstructing Knowledge Passport from evidence records...</p>
        </div>
      ) : activeEmployee && passportData ? (
        <div className="space-y-6">
          {/* Header Profile Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xs">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 rounded-2xl bg-linear-to-br from-teal-500 to-emerald-600 flex items-center justify-center text-slate-950 font-black text-xl shadow-lg shadow-teal-500/20">
                  {activeEmployee.name.split(' ').map((n) => n[0]).join('')}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-white">{activeEmployee.name}</h2>
                    <span className="text-xs font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                      {activeEmployee.employee_id_code}
                    </span>
                    <span className="text-xs text-slate-400">• {activeEmployee.department}</span>
                  </div>
                  <p className="text-xs text-teal-300 font-medium mt-0.5">{activeEmployee.role_title}</p>
                  <p className="text-xs text-slate-400 mt-1 max-w-2xl">
                    {activeEmployee.contribution_summary || 'No summary recorded.'}
                  </p>
                  {activeEmployee.successor_name && (
                    <div className="mt-2 text-xs flex items-center gap-1.5 text-amber-300">
                      <UserPlus className="w-3.5 h-3.5" />
                      <span>Assigned Successor: <strong>{activeEmployee.successor_name}</strong></span>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2.5">
                <button
                  onClick={handleReconstruct}
                  disabled={isReconstructing}
                  className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-teal-300 text-xs font-medium rounded-xl border border-slate-700 flex items-center gap-1.5 transition-all shadow-xs disabled:opacity-50"
                >
                  <Sparkles className={`w-3.5 h-3.5 ${isReconstructing ? 'animate-spin text-teal-400' : ''}`} />
                  {isReconstructing ? 'Reconstructing...' : 'Reconstruct (AI)'}
                </button>
                <button
                  onClick={() => setShowInitiateModal(true)}
                  className="px-3.5 py-2 bg-teal-600 hover:bg-teal-500 text-white text-xs font-medium rounded-xl flex items-center gap-1.5 transition-all shadow-xs"
                >
                  <ArrowRight className="w-3.5 h-3.5" />
                  Initiate Handover
                </button>
              </div>
            </div>

            {/* Quick Metrics Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-5 pt-4 border-t border-slate-800/80">
              <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Commits</div>
                <div className="text-base font-bold text-white mt-0.5 flex items-center gap-1">
                  <GitCommit className="w-4 h-4 text-teal-400" />
                  {passportData.commits.length}
                </div>
              </div>
              <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Pull Requests</div>
                <div className="text-base font-bold text-white mt-0.5 flex items-center gap-1">
                  <GitPullRequest className="w-4 h-4 text-purple-400" />
                  {passportData.pull_requests.length}
                </div>
              </div>
              <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">APIs Authored</div>
                <div className="text-base font-bold text-white mt-0.5 flex items-center gap-1">
                  <Code2 className="w-4 h-4 text-sky-400" />
                  {passportData.api_endpoints.length}
                </div>
              </div>
              <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Bugs & Debt</div>
                <div className="text-base font-bold text-amber-300 mt-0.5 flex items-center gap-1">
                  <Bug className="w-4 h-4 text-amber-400" />
                  {passportData.bugs_and_debt.length}
                </div>
              </div>
              <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Active Blockers</div>
                <div className="text-base font-bold text-rose-300 mt-0.5 flex items-center gap-1">
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                  {passportData.blockers.length}
                </div>
              </div>
              <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Knowledge Gaps</div>
                <div className="text-base font-bold text-indigo-300 mt-0.5 flex items-center gap-1">
                  <ShieldCheck className="w-4 h-4 text-indigo-400" />
                  {passportData.knowledge_gaps.length}
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-1 overflow-x-auto border-b border-slate-800 pb-px text-xs font-medium">
            {[
              { id: 'overview', label: 'Overview', icon: FileText },
              { id: 'timeline', label: `Timeline (${passportData.timeline.length})`, icon: Clock },
              { id: 'code', label: `Commits & PRs (${passportData.commits.length + passportData.pull_requests.length})`, icon: GitCommit },
              { id: 'apis', label: `API Handover (${passportData.api_endpoints.length})`, icon: Code2 },
              { id: 'database', label: `Database (${passportData.schema_records.length})`, icon: Database },
              { id: 'bugs', label: `Bugs & Debt (${passportData.bugs_and_debt.length})`, icon: Bug },
              { id: 'blockers', label: `Blockers & Gaps (${passportData.blockers.length + passportData.knowledge_gaps.length})`, icon: AlertTriangle },
              { id: 'checklist', label: `Continuation Plan (${passportData.continuation_plan.length})`, icon: CheckSquare },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-2 px-3.5 py-2.5 rounded-t-lg transition-colors whitespace-nowrap ${
                    isActive
                      ? 'bg-slate-800 text-teal-300 border-b-2 border-teal-500 font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                {/* Core Responsibilities */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <h3 className="text-sm font-bold text-white mb-3">Core Scope & Responsibilities</h3>
                  <div className="flex flex-wrap gap-2">
                    {activeEmployee.responsibilities.map((r, i) => (
                      <span key={i} className="px-3 py-1 bg-slate-800 text-slate-300 rounded-lg text-xs border border-slate-700/80">
                        {r}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Key Technical Artifacts summary */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <h3 className="text-sm font-bold text-white mb-3">High-Impact Deliverables</h3>
                  <div className="space-y-3">
                    {passportData.api_endpoints.slice(0, 3).map((api) => (
                      <div key={api.id} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                            api.method === 'GET' ? 'bg-sky-500/20 text-sky-400' :
                            api.method === 'POST' ? 'bg-emerald-500/20 text-emerald-400' :
                            api.method === 'PUT' ? 'bg-amber-500/20 text-amber-400' :
                            'bg-rose-500/20 text-rose-400'
                          }`}>
                            {api.method}
                          </span>
                          <div>
                            <div className="text-xs font-mono font-medium text-slate-200">{api.endpoint_path}</div>
                            <div className="text-[11px] text-slate-400">{api.description}</div>
                          </div>
                        </div>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                          api.implementation_status === 'COMPLETED' ? 'bg-teal-500/20 text-teal-300' : 'bg-amber-500/20 text-amber-300'
                        }`}>
                          {api.implementation_status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Sidebar: Critical Handover Risks */}
              <div className="space-y-6">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <div className="flex items-center gap-2 text-rose-400 text-xs font-bold uppercase tracking-wider mb-3">
                    <AlertTriangle className="w-4 h-4" />
                    Immediate Day 1 Attention
                  </div>
                  <div className="space-y-3">
                    {passportData.bugs_and_debt.map((bug) => (
                      <div key={bug.id} className="p-3 bg-rose-950/20 border border-rose-900/30 rounded-lg">
                        <div className="flex items-center justify-between text-[10px] font-bold">
                          <span className="text-rose-300">{bug.classification}</span>
                          <span className="px-1.5 py-0.5 bg-rose-500/20 text-rose-300 rounded uppercase">{bug.severity}</span>
                        </div>
                        <div className="text-xs font-medium text-slate-200 mt-1">{bug.title}</div>
                        <p className="text-[11px] text-slate-400 mt-1">{bug.recommended_next_action}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <div className="flex items-center gap-2 text-amber-400 text-xs font-bold uppercase tracking-wider mb-3">
                    <ShieldCheck className="w-4 h-4" />
                    Tacit Knowledge Gaps Identified
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    AI identified <strong>{passportData.knowledge_gaps.length} areas</strong> where Rahul held exclusive institutional knowledge with minimal repository documentation.
                  </p>
                  <div className="mt-3 space-y-2">
                    {passportData.knowledge_gaps.map((gap) => (
                      <div key={gap.id} className="text-xs text-slate-300 p-2 bg-slate-950/60 rounded border border-slate-800">
                        • {gap.title}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: TIMELINE */}
          {activeTab === 'timeline' && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h3 className="text-sm font-bold text-white mb-4">Evidence-Verified Work Timeline</h3>
              <div className="relative border-l-2 border-slate-800 ml-4 space-y-6">
                {passportData.timeline.map((evt) => (
                  <div key={evt.id} className="relative pl-6">
                    <div className="absolute -left-1.5 top-1 w-3 h-3 rounded-full bg-teal-500 border-2 border-slate-900" />
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-white">{evt.title}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                          {evt.event_type}
                        </span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                          evt.verification_status === 'VERIFIED'
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        }`}>
                          {evt.verification_status}
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-500 font-mono">{evt.timestamp}</span>
                    </div>
                    {evt.description && (
                      <p className="text-xs text-slate-400 mt-1">{evt.description}</p>
                    )}
                    {evt.source_reference && (
                      <div className="text-[10px] text-teal-400/90 font-mono mt-1 flex items-center gap-1">
                        <span>Source:</span> {evt.source_reference}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: COMMITS & PRS */}
          {activeTab === 'code' && (
            <div className="space-y-6">
              {/* Commits */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                  <GitCommit className="w-4 h-4 text-teal-400" />
                  Authored Commits ({passportData.commits.length})
                </h3>
                <div className="space-y-2">
                  {passportData.commits.map((c) => (
                    <div key={c.id} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 hover:border-slate-700 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-start gap-3">
                        <span className="font-mono text-xs text-teal-400 font-bold bg-teal-500/10 px-2 py-1 rounded border border-teal-500/20">
                          {c.commit_hash.slice(0, 7)}
                        </span>
                        <div>
                          <div className="text-xs font-semibold text-slate-200">{c.message}</div>
                          <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                            Branch: {c.branch} • {c.changed_files?.length || 0} files changed (+{c.insertions || 0} / -{c.deletions || 0})
                          </div>
                        </div>
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono whitespace-nowrap">
                        {c.timestamp ? new Date(c.timestamp).toLocaleDateString() : 'Recent'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Pull Requests */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                  <GitPullRequest className="w-4 h-4 text-purple-400" />
                  Pull Requests Authored ({passportData.pull_requests.length})
                </h3>
                <div className="space-y-3">
                  {passportData.pull_requests.map((pr) => (
                    <div key={pr.id} className="p-3.5 bg-slate-950/60 rounded-lg border border-slate-800">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono font-bold text-purple-400">PR #{pr.pr_number}</span>
                          <h4 className="text-xs font-bold text-slate-200">{pr.title}</h4>
                        </div>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold uppercase ${
                          pr.is_merged ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'bg-emerald-500/20 text-emerald-300'
                        }`}>
                          {pr.is_merged ? 'MERGED' : 'OPEN'}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1.5">{pr.description}</p>
                      <div className="flex flex-wrap items-center gap-3 mt-2 pt-2 border-t border-slate-800/80 text-[10px] text-slate-500">
                        <span>Base: <strong className="text-slate-400">{pr.target_branch}</strong></span>
                        <span>Head: <strong className="text-slate-400">{pr.source_branch}</strong></span>
                        {pr.review_notes && (
                          <span className="text-teal-400 font-mono">{pr.review_notes}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: API HANDOVER */}
          {activeTab === 'apis' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white">Full API Endpoints Inventory</h3>
                <span className="text-xs text-slate-400">Total Authored: {passportData.api_endpoints.length}</span>
              </div>
              <div className="space-y-3">
                {passportData.api_endpoints.map((api) => (
                  <div key={api.id} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-3">
                        <span className={`px-2.5 py-1 rounded text-xs font-mono font-bold ${
                          api.method === 'GET' ? 'bg-sky-500/20 text-sky-400' :
                          api.method === 'POST' ? 'bg-emerald-500/20 text-emerald-400' :
                          api.method === 'PUT' ? 'bg-amber-500/20 text-amber-400' :
                          'bg-rose-500/20 text-rose-400'
                        }`}>
                          {api.method}
                        </span>
                        <span className="font-mono text-sm font-bold text-white">{api.endpoint_path}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {api.auth_required && (
                          <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                            Auth Required
                          </span>
                        )}
                        <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase ${
                          api.implementation_status === 'COMPLETED'
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : 'bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse'
                        }`}>
                          {api.implementation_status}
                        </span>
                      </div>
                    </div>

                    <p className="text-xs text-slate-300 mt-2">{api.description}</p>

                    {(api.request_body || api.request_params) && (
                      <div className="mt-3">
                        <div className="text-[10px] text-slate-400 uppercase font-semibold mb-1">Request Payload Schema</div>
                        <pre className="bg-slate-950 p-2.5 rounded-lg text-[11px] text-teal-300 font-mono overflow-x-auto border border-slate-800">
                          {JSON.stringify(api.request_body || api.request_params, null, 2)}
                        </pre>
                      </div>
                    )}

                    {api.frontend_callers && api.frontend_callers.length > 0 && (
                      <div className="mt-2 text-[11px] text-slate-400">
                        <strong>Downstream Callers:</strong> {api.frontend_callers.join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 5: DATABASE */}
          {activeTab === 'database' && (
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-white">Database Schemas & Storage Architecture</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {passportData.schema_records.map((schema) => (
                  <div key={schema.id} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Database className="w-4 h-4 text-teal-400" />
                        <span className="text-xs font-mono font-bold text-white">{schema.table_name}</span>
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                        {schema.model_name}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-2">{schema.description}</p>
                    {schema.migration_script && (
                      <div className="mt-2 text-[10px] font-mono text-teal-400 bg-slate-950 p-1.5 rounded border border-slate-800">
                        Migration: {schema.migration_script}
                      </div>
                    )}
                    {schema.columns && schema.columns.length > 0 && (
                      <div className="mt-2 text-[11px] text-slate-300">
                        <strong>Key Columns:</strong> {schema.columns.map(c => c.name).join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 6: BUGS & DEBT */}
          {activeTab === 'bugs' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white">Unresolved Bugs & Technical Debt</h3>
                  <p className="text-xs text-slate-400">Authoritative classification of defects left in progress</p>
                </div>
              </div>

              <div className="space-y-4">
                {passportData.bugs_and_debt.map((bug) => (
                  <div key={bug.id} className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                          bug.classification === 'CONFIRMED UNRESOLVED'
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                            : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        }`}>
                          {bug.classification}
                        </span>
                        <h4 className="text-sm font-bold text-white">{bug.title}</h4>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 font-mono uppercase font-bold">
                          {bug.severity} Severity
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                          Confidence: {bug.confidence_level}
                        </span>
                      </div>
                    </div>

                    <p className="text-xs text-slate-300 mt-2">{bug.description}</p>

                    {bug.file_path && (
                      <div className="mt-2 text-xs font-mono text-teal-400 flex items-center gap-1.5">
                        <Code2 className="w-3.5 h-3.5" />
                        <span>{bug.file_path}{bug.line_number ? `:${bug.line_number}` : ''}</span>
                      </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4 pt-3 border-t border-slate-800">
                      <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800">
                        <div className="text-[10px] font-semibold text-slate-400 uppercase">Investigation Performed</div>
                        <p className="text-xs text-slate-300 mt-1">{bug.investigation_performed || 'None documented'}</p>
                      </div>
                      <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800">
                        <div className="text-[10px] font-semibold text-slate-400 uppercase">Why Unresolved</div>
                        <p className="text-xs text-amber-300 mt-1">{bug.why_unresolved || 'Time constraints'}</p>
                      </div>
                      <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800">
                        <div className="text-[10px] font-semibold text-teal-400 uppercase">Recommended Next Action</div>
                        <p className="text-xs text-teal-200 mt-1">{bug.recommended_next_action || 'Review test cases'}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 7: BLOCKERS & GAPS */}
          {activeTab === 'blockers' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Blockers */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                  Active Blockers ({passportData.blockers.length})
                </h3>
                <div className="space-y-3">
                  {passportData.blockers.map((b) => (
                    <div key={b.id} className="p-3.5 bg-rose-950/20 border border-rose-900/30 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-200">{b.title}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-semibold uppercase">
                          {b.status}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1">{b.description}</p>
                      {b.external_dependency && (
                        <div className="mt-2 text-[10px] text-amber-400">
                          <strong>Dependency:</strong> {b.external_dependency}
                        </div>
                      )}
                      {b.required_assistance && (
                        <div className="text-[10px] text-slate-300 mt-0.5">
                          <strong>Action Required:</strong> {b.required_assistance}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Knowledge Gaps */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-indigo-400" />
                  Identified Tacit Knowledge Gaps ({passportData.knowledge_gaps.length})
                </h3>
                <div className="space-y-3">
                  {passportData.knowledge_gaps.map((g) => (
                    <div key={g.id} className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-200">{g.title}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-semibold uppercase">
                          {g.severity}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1">{g.description}</p>
                      {g.affected_component && (
                        <div className="mt-2 text-[10px] text-teal-400 font-mono">
                          Affected Component: {g.affected_component}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 8: CONTINUATION PLAN */}
          {activeTab === 'checklist' && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h3 className="text-sm font-bold text-white">Successor Continuation Action Plan</h3>
                  <p className="text-xs text-slate-400">Structured phased tasks for seamless project takeover</p>
                </div>
                <div className="text-xs text-teal-400 font-mono">
                  {passportData.continuation_plan.filter(i => i.is_completed).length} / {passportData.continuation_plan.length} Completed
                </div>
              </div>

              {/* Group By Phase */}
              {['DAY_1', 'DAY_2_3', 'WEEK_1', 'DAY_30'].map((phaseKey) => {
                const items = passportData.continuation_plan.filter((i) => i.phase === phaseKey);
                if (items.length === 0) return null;
                const phaseTitle =
                  phaseKey === 'DAY_1' ? 'Phase 1: Day 1 Immediate Onboarding' :
                  phaseKey === 'DAY_2_3' ? 'Phase 2: Days 2–3 Bug Resolution & Pipeline Setup' :
                  phaseKey === 'WEEK_1' ? 'Phase 3: Week 1 Integration & Feature Continuation' :
                  'Phase 4: Day 30+ Long-Term Architectural Roadmap';

                return (
                  <div key={phaseKey} className="space-y-3">
                    <div className="text-xs font-bold text-slate-300 uppercase tracking-wider border-b border-slate-800 pb-1.5 flex items-center justify-between">
                      <span>{phaseTitle}</span>
                      <span className="text-[10px] text-slate-500 font-mono font-normal">
                        {items.filter(i => i.is_completed).length}/{items.length} Done
                      </span>
                    </div>

                    <div className="space-y-2">
                      {items.map((item) => (
                        <div
                          key={item.id}
                          onClick={() => handleToggleChecklist(item.id)}
                          className={`p-3 rounded-lg border transition-all cursor-pointer flex items-start gap-3 ${
                            item.is_completed
                              ? 'bg-teal-950/20 border-teal-800/40 opacity-75'
                              : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                          }`}
                        >
                          <button className="mt-0.5 text-teal-400">
                            {item.is_completed ? (
                              <CheckSquare className="w-4 h-4 text-teal-400" />
                            ) : (
                              <Square className="w-4 h-4 text-slate-600" />
                            )}
                          </button>
                          <div className="flex-1">
                            <div className="flex items-center justify-between">
                              <span className={`text-xs font-semibold ${item.is_completed ? 'line-through text-slate-500' : 'text-slate-200'}`}>
                                {item.title}
                              </span>
                              <span className={`text-[10px] px-2 py-0.5 rounded font-mono uppercase ${
                                item.priority === 'critical' ? 'bg-rose-500/20 text-rose-300' : 'bg-slate-800 text-slate-400'
                              }`}>
                                {item.priority}
                              </span>
                            </div>
                            {item.description && (
                              <p className="text-[11px] text-slate-400 mt-1">{item.description}</p>
                            )}
                            {item.relevant_files && item.relevant_files.length > 0 && (
                              <div className="mt-2 flex flex-wrap gap-1">
                                {item.relevant_files.map((f, fi) => (
                                  <span key={fi} className="text-[10px] font-mono px-1.5 py-0.5 bg-slate-900 text-teal-300 rounded border border-slate-800">
                                    {f}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        <div className="p-12 text-center text-slate-500 bg-slate-900 border border-slate-800 rounded-2xl">
          <p className="text-xs">No employee profile selected.</p>
        </div>
      )}

      {/* Handover Initiation Modal */}
      {showInitiateModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Initiate Employee Handover</h3>
            <p className="text-xs text-slate-400 mt-1">
              Transition institutional knowledge from <strong>{activeEmployee?.name}</strong> to a designated successor.
            </p>

            <form onSubmit={handleInitiateHandover} className="mt-4 space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-300">Designated Successor</label>
                <select
                  value={successorId}
                  onChange={(e) => setSuccessorId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full mt-1.5 bg-slate-800 text-slate-200 text-xs px-3 py-2.5 rounded-lg border border-slate-700 focus:outline-hidden focus:border-teal-500"
                >
                  <option value="">Select successor...</option>
                  {employees
                    .filter((e) => e.id !== selectedEmployeeId)
                    .map((e) => (
                      <option key={e.id} value={e.id}>
                        {e.name} — {e.role_title}
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300">Transition Context & Instructions</label>
                <textarea
                  value={handoverNotes}
                  onChange={(e) => setHandoverNotes(e.target.value)}
                  placeholder="Specific focus areas, priority repositories, or upcoming deployment dates..."
                  rows={4}
                  className="w-full mt-1.5 bg-slate-800 text-slate-200 text-xs p-3 rounded-lg border border-slate-700 focus:outline-hidden focus:border-teal-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowInitiateModal(false)}
                  className="px-4 py-2 text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold rounded-lg shadow-sm"
                >
                  Confirm & Initiate Handover
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
