import React, { useState, useEffect } from 'react';
import {
  Compass,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Code2,
  GitCommit,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckSquare,
  Square,
  FileCheck2,
  MessageSquareText,
  UserCheck
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { projectApi, employeeApi, askAiApi } from '../services/api';
import {
  Project,
  EmployeeProfile,
  EmployeePassportData,
  ContinuationActionItem,
  AskAIResponse
} from '../types';

export const IncomingWorkspacePage: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [employees, setEmployees] = useState<EmployeeProfile[]>([]);
  const [departingEmployee, setDepartingEmployee] = useState<EmployeeProfile | null>(null);
  const [incomingEmployee, setIncomingEmployee] = useState<EmployeeProfile | null>(null);
  const [passportData, setPassportData] = useState<EmployeePassportData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Acknowledgment Modal
  const [showAcknowledgeModal, setShowAcknowledgeModal] = useState(false);
  const [acknowledgeNotes, setAcknowledgeNotes] = useState('');
  const [isAcknowledging, setIsAcknowledging] = useState(false);
  const [acknowledgementInfo, setAcknowledgementInfo] = useState<{
    acknowledged_at: string;
    acknowledged_by: string;
  } | null>(null);

  // Inline Ask AI
  const [quickQuestion, setQuickQuestion] = useState('');
  const [aiAnswer, setAiAnswer] = useState<AskAIResponse | null>(null);
  const [isAsking, setIsAsking] = useState(false);

  useEffect(() => {
    projectApi.list().then((projs) => {
      setProjects(projs);
      if (projs.length > 0) setSelectedProjectId(projs[0].id);
    }).catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedProjectId) return;
    employeeApi.listByProject(selectedProjectId).then((emps) => {
      setEmployees(emps);
      const departing = emps.find((e) => e.name.toLowerCase().includes('rahul')) || emps[0];
      const incoming = emps.find((e) => e.name.toLowerCase().includes('maya')) || emps.find((e) => e.id !== departing?.id);
      setDepartingEmployee(departing || null);
      setIncomingEmployee(incoming || null);
    }).catch(console.error);
  }, [selectedProjectId]);

  useEffect(() => {
    if (!departingEmployee) return;
    setIsLoading(true);
    employeeApi.getPassport(departingEmployee.id).then((data) => {
      setPassportData(data);
      if (departingEmployee.handover_status === 'COMPLETED' || departingEmployee.handover_status === 'ACKNOWLEDGED') {
        setAcknowledgementInfo({
          acknowledged_at: new Date().toISOString(),
          acknowledged_by: incomingEmployee?.name || 'Incoming Developer'
        });
      }
    }).catch(console.error).finally(() => setIsLoading(false));
  }, [departingEmployee, incomingEmployee]);

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
      console.error(err);
    }
  };

  const handleAcknowledge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!departingEmployee) return;
    try {
      setIsAcknowledging(true);
      const res = await employeeApi.acknowledgeHandover(departingEmployee.id, {
        comments: acknowledgeNotes
      });
      setAcknowledgementInfo({
        acknowledged_at: res.acknowledged_at,
        acknowledged_by: res.acknowledged_by
      });
      setShowAcknowledgeModal(false);
      // Refresh passport
      const fresh = await employeeApi.getPassport(departingEmployee.id);
      setPassportData(fresh);
    } catch (err) {
      console.error(err);
    } finally {
      setIsAcknowledging(false);
    }
  };

  const handleQuickAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjectId || !quickQuestion.trim()) return;
    try {
      setIsAsking(true);
      const res = await askAiApi.ask({
        project_id: selectedProjectId,
        question: quickQuestion,
        employee_id: departingEmployee?.id,
        role_scope: 'BACKEND'
      });
      setAiAnswer(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsAsking(false);
    }
  };

  const completedActions = passportData?.continuation_plan.filter((i) => i.is_completed).length || 0;
  const totalActions = passportData?.continuation_plan.length || 0;
  const progressPercent = totalActions > 0 ? Math.round((completedActions / totalActions) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              Incoming Developer Workspace
            </span>
            <span className="text-xs text-slate-400 font-mono">Day-1 Productivity Guarantee</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-1 flex items-center gap-2">
            <Compass className="w-7 h-7 text-emerald-400" />
            Project Continuity Hub
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Tailored continuation workspace for incoming engineer <strong>{incomingEmployee?.name || 'Maya Patel'}</strong> taking over from <strong>{departingEmployee?.name || 'Rahul Sharma'}</strong>.
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

      {/* Handover Hero Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-teal-500/5 rounded-full blur-3xl -z-10" />
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300">
                Transition Handover Package
              </span>
              {acknowledgementInfo ? (
                <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  Handover Formally Acknowledged
                </span>
              ) : (
                <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1.5 animate-pulse">
                  <Clock className="w-3.5 h-3.5 text-amber-400" />
                  Review & Sign-Off Pending
                </span>
              )}
            </div>
            <h2 className="text-xl font-bold text-white">
              {incomingEmployee?.name} ← {departingEmployee?.name} Handover
            </h2>
            <p className="text-xs text-slate-400 max-w-2xl leading-relaxed">
              Rahul has transferred ownership of the backend core services, authentication architecture, and bulk data pipelines. Complete the prioritized Day-1 through Day-30 continuation roadmap below.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3">
            {!acknowledgementInfo ? (
              <button
                onClick={() => setShowAcknowledgeModal(true)}
                className="w-full sm:w-auto px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/20 transition-all"
              >
                <FileCheck2 className="w-4 h-4" />
                Sign & Acknowledge Handover
              </button>
            ) : (
              <div className="p-3 bg-emerald-950/30 border border-emerald-800/40 rounded-xl text-left">
                <div className="text-[10px] text-emerald-400 uppercase font-bold">Signed Off</div>
                <div className="text-xs font-mono text-slate-300">
                  {new Date(acknowledgementInfo.acknowledged_at).toLocaleString()}
                </div>
              </div>
            )}
            <button
              onClick={() => navigate('/ask-ai')}
              className="w-full sm:w-auto px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-teal-300 text-xs font-semibold rounded-xl border border-slate-700 flex items-center justify-center gap-2 transition-all"
            >
              <MessageSquareText className="w-4 h-4 text-teal-400" />
              Ask Project AI
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-6 pt-5 border-t border-slate-800/80">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="font-semibold text-slate-300">Takeover Readiness Progress</span>
            <span className="font-mono text-teal-400 font-bold">{progressPercent}% ({completedActions}/{totalActions} tasks)</span>
          </div>
          <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-linear-to-r from-teal-500 to-emerald-400 rounded-full transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Main 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Phased Checklist */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <CheckSquare className="w-5 h-5 text-teal-400" />
                  Phased Continuation Checklist
                </h3>
                <p className="text-xs text-slate-400">Click to check off tasks as you onboard</p>
              </div>
            </div>

            {isLoading ? (
              <div className="py-12 text-center text-slate-500">
                <div className="inline-block w-5 h-5 border-2 border-teal-500 border-t-transparent rounded-full animate-spin mb-2" />
                <p className="text-xs">Loading continuation plan...</p>
              </div>
            ) : passportData?.continuation_plan ? (
              ['DAY_1', 'DAY_2_3', 'WEEK_1', 'DAY_30'].map((phaseKey) => {
                const items = passportData.continuation_plan.filter((i) => i.phase === phaseKey);
                if (items.length === 0) return null;
                const phaseBadge =
                  phaseKey === 'DAY_1' ? 'Day 1 — Immediate Takeover' :
                  phaseKey === 'DAY_2_3' ? 'Days 2–3 — Bug Fixing & Local Integration' :
                  phaseKey === 'WEEK_1' ? 'Week 1 — Feature Completion' :
                  'Day 30 — Scalability & Architecture';

                return (
                  <div key={phaseKey} className="space-y-3">
                    <div className="flex items-center justify-between bg-slate-950/70 px-3.5 py-2 rounded-lg border border-slate-800">
                      <span className="text-xs font-bold text-teal-300 font-mono">{phaseBadge}</span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {items.filter(i => i.is_completed).length}/{items.length} Completed
                      </span>
                    </div>

                    <div className="space-y-2">
                      {items.map((item) => (
                        <div
                          key={item.id}
                          onClick={() => handleToggleChecklist(item.id)}
                          className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-start gap-3.5 ${
                            item.is_completed
                              ? 'bg-slate-950/40 border-teal-900/40 opacity-75'
                              : 'bg-slate-950/90 border-slate-800 hover:border-slate-700 hover:bg-slate-900/60'
                          }`}
                        >
                          <button className="mt-0.5 text-teal-400">
                            {item.is_completed ? (
                              <CheckSquare className="w-4 h-4 text-emerald-400" />
                            ) : (
                              <Square className="w-4 h-4 text-slate-600" />
                            )}
                          </button>
                          <div className="flex-1">
                            <div className="flex items-center justify-between">
                              <span className={`text-xs font-semibold ${item.is_completed ? 'line-through text-slate-500' : 'text-slate-200'}`}>
                                {item.title}
                              </span>
                              <span className={`text-[10px] px-2 py-0.5 rounded font-mono uppercase font-bold ${
                                item.priority === 'critical' ? 'bg-rose-500/20 text-rose-300' : 'bg-slate-800 text-slate-400'
                              }`}>
                                {item.priority}
                              </span>
                            </div>
                            {item.description && (
                              <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">{item.description}</p>
                            )}
                            {item.relevant_files && item.relevant_files.length > 0 && (
                              <div className="mt-2 flex flex-wrap gap-1.5">
                                {item.relevant_files.map((f, fi) => (
                                  <span key={fi} className="text-[10px] font-mono px-2 py-0.5 bg-slate-900 text-teal-300 rounded border border-slate-800">
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
              })
            ) : null}
          </div>
        </div>

        {/* Right Col: Instant Project AI & Immediate Attention */}
        <div className="space-y-6">
          {/* Quick Ask AI Box */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-teal-400 text-xs font-bold uppercase tracking-wider">
              <Sparkles className="w-4 h-4" />
              Ask Rahul's Codebase
            </div>
            <p className="text-xs text-slate-400">
              Query questions about Rahul's PRs, configuration quirks, or bugs with grounded citations.
            </p>

            <form onSubmit={handleQuickAsk} className="space-y-2">
              <input
                type="text"
                value={quickQuestion}
                onChange={(e) => setQuickQuestion(e.target.value)}
                placeholder="e.g. Why is token blacklist failing in auth?"
                className="w-full bg-slate-800 text-slate-200 text-xs p-2.5 rounded-lg border border-slate-700 focus:outline-hidden focus:border-teal-500"
              />
              <button
                type="submit"
                disabled={isAsking || !quickQuestion.trim()}
                className="w-full py-2 bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 disabled:opacity-50 transition-colors"
              >
                <Sparkles className={`w-3.5 h-3.5 ${isAsking ? 'animate-spin' : ''}`} />
                {isAsking ? 'Consulting Project AI...' : 'Ask Continuity AI'}
              </button>
            </form>

            {aiAnswer && (
              <div className="p-3 bg-slate-950 rounded-xl border border-teal-500/30 text-xs space-y-2 animate-fadeIn">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-teal-400 uppercase">AI Answer</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-teal-500/20 text-teal-300 font-mono font-bold">
                    {aiAnswer.confidence} Confidence
                  </span>
                </div>
                <p className="text-slate-300 leading-relaxed text-[11px]">{aiAnswer.answer}</p>
                {aiAnswer.citations.length > 0 && (
                  <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-400">
                    <span className="font-semibold text-slate-300">Citations: </span>
                    {aiAnswer.citations.map((c, ci) => (
                      <span key={ci} className="text-teal-400 font-mono mr-2">[{c.reference}]</span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Critical Bug Debt Callout */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center gap-2 text-rose-400 text-xs font-bold uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4" />
              Day-1 Bug Priority
            </div>
            {passportData?.bugs_and_debt.map((bug) => (
              <div key={bug.id} className="p-3 bg-rose-950/20 border border-rose-900/30 rounded-xl text-xs space-y-1">
                <div className="flex items-center justify-between font-bold">
                  <span className="text-rose-300">{bug.title}</span>
                  <span className="text-[10px] px-1.5 py-0.5 bg-rose-500/20 text-rose-400 rounded uppercase">
                    {bug.severity}
                  </span>
                </div>
                <div className="text-[11px] font-mono text-slate-400">{bug.file_path}:{bug.line_number}</div>
                <p className="text-[11px] text-slate-300 mt-1">{bug.recommended_next_action}</p>
              </div>
            ))}
          </div>

          {/* Deliverable Endpoints */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center gap-2 text-sky-400 text-xs font-bold uppercase tracking-wider">
              <Code2 className="w-4 h-4" />
              Incomplete APIs To Finalize
            </div>
            {passportData?.api_endpoints
              .filter((a) => a.implementation_status !== 'COMPLETED')
              .map((api) => (
                <div key={api.id} className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400">
                      {api.method}
                    </span>
                    <span className="font-mono text-slate-200 text-[11px] font-bold">{api.endpoint_path}</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">{api.description}</p>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Handover Sign-off Modal */}
      {showAcknowledgeModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <FileCheck2 className="w-5 h-5 text-emerald-400" />
              Sign & Acknowledge Handover Receipt
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              By confirming, <strong>{incomingEmployee?.name}</strong> officially accepts custody of the project artifacts, database models, and unresolved debt left by <strong>{departingEmployee?.name}</strong>.
            </p>

            <form onSubmit={handleAcknowledge} className="mt-4 space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-300">Acceptance Notes / Transition Remarks</label>
                <textarea
                  value={acknowledgeNotes}
                  onChange={(e) => setAcknowledgeNotes(e.target.value)}
                  placeholder="e.g. Reviewed Day 1 checklist, validated auth test failures, taking ownership of sprint tickets..."
                  rows={4}
                  className="w-full mt-1.5 bg-slate-800 text-slate-200 text-xs p-3 rounded-lg border border-slate-700 focus:outline-hidden focus:border-teal-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAcknowledgeModal(false)}
                  className="px-4 py-2 text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isAcknowledging}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow-sm flex items-center gap-1.5 disabled:opacity-50"
                >
                  {isAcknowledging ? 'Recording Signature...' : 'Confirm Sign-Off'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
