import React, { useEffect, useState } from 'react';
import {
  FileCheck2,
  Download,
  Plus,
  CheckCircle2,
  XCircle,
  FileText,
  Clock,
  Layers,
  ShieldCheck,
  Printer,
  ChevronRight,
  Eye,
  Check
} from 'lucide-react';
import { projectApi, handoverApi } from '../services/api';
import { Project, HandoverReport } from '../types';
import { Badge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';

export const HandoverReportsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [reports, setReports] = useState<HandoverReport[]>([]);
  const [activeReport, setActiveReport] = useState<HandoverReport | null>(null);
  const [loading, setLoading] = useState(true);

  // View mode toggle for active report
  const [viewMode, setViewMode] = useState<'incoming_member_view' | 'pm_view'>('incoming_member_view');

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      loadReports(selectedProjectId);
    }
  }, [selectedProjectId]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const projs = await projectApi.list();
      setProjects(projs);
      if (projs.length > 0) {
        setSelectedProjectId(projs[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadReports = async (projId: number) => {
    try {
      setLoading(true);
      const list = await handoverApi.list(projId);
      setReports(list);
      if (list.length > 0) {
        setActiveReport(list[0]);
        setViewMode(list[0].view_mode as any || 'incoming_member_view');
      } else {
        setActiveReport(null);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (mode: 'incoming_member_view' | 'pm_view') => {
    if (!selectedProjectId) return;
    try {
      setLoading(true);
      const created = await handoverApi.generate(selectedProjectId, {
        title: `Knowledge Handover & Continuity Plan (v${reports.length + 1})`,
        view_mode: mode,
      });
      setReports([created, ...reports]);
      setActiveReport(created);
      setViewMode(mode);
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
      a.download = `Continuum_Handover_v${activeReport?.version || 1}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      console.error(err);
    }
  };

  const handleApprove = async () => {
    if (!activeReport) return;
    try {
      const updated = await handoverApi.approve(activeReport.id, 'Inspected and approved by reviewer.');
      setActiveReport(updated);
      setReports(reports.map((r) => (r.id === updated.id ? updated : r)));
    } catch (err) {
      console.error(err);
    }
  };

  const handleReject = async () => {
    if (!activeReport) return;
    const reason = window.prompt('Enter reason for revision request / rejection:');
    if (!reason) return;
    try {
      const updated = await handoverApi.reject(activeReport.id, reason);
      setActiveReport(updated);
      setReports(reports.map((r) => (r.id === updated.id ? updated : r)));
    } catch (err) {
      console.error(err);
    }
  };

  const content = activeReport?.report_content || {};

  return (
    <div className="space-y-6">
      {/* Header and Project Select */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Handover Report Generator</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Generates structured 14-section dossiers, downloadable as high-fidelity ReportLab PDFs.
          </p>
        </div>

        {projects.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-slate-600">Active Project:</span>
            <select
              value={selectedProjectId || ''}
              onChange={(e) => setSelectedProjectId(Number(e.target.value))}
              className="px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500 font-semibold text-slate-800"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} {p.is_demo ? '(DEMO)' : ''}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {reports.length === 0 ? (
        <EmptyState
          icon={FileCheck2}
          title="No handover dossiers generated yet"
          description="Synthesize an evidence-backed continuation report for the incoming developer."
          actionText="Generate Incoming Member View"
          onAction={() => handleGenerate('incoming_member_view')}
          secondaryActionText="Generate PM Audit View"
          onSecondaryAction={() => handleGenerate('pm_view')}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Reports History Sidebar */}
          <div className="lg:col-span-1 space-y-3">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Versions ({reports.length})
                </span>
                <button
                  onClick={() => handleGenerate('incoming_member_view')}
                  className="p-1 text-teal-600 hover:text-teal-700 rounded hover:bg-teal-50"
                  title="Generate new version"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2">
                {reports.map((r) => {
                  const isSelected = activeReport?.id === r.id;
                  return (
                    <div
                      key={r.id}
                      onClick={() => {
                        setActiveReport(r);
                        setViewMode(r.view_mode as any || 'incoming_member_view');
                      }}
                      className={`p-3 rounded-lg border text-xs cursor-pointer transition-all ${
                        isSelected
                          ? 'border-teal-500 bg-teal-50/20 text-slate-950 font-semibold shadow-xs'
                          : 'border-slate-100 hover:border-slate-200 text-slate-600'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="truncate max-w-[130px]">v{r.version}: {r.title}</span>
                        <Badge variant={r.status as any}>{r.status}</Badge>
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {new Date(r.created_at).toLocaleDateString()} • {r.creator_name}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Dossier Viewer (14 Sections) */}
          <div className="lg:col-span-3 space-y-4">
            {activeReport && (
              <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-6">
                {/* Dossier Action Bar */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-200 gap-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h2 className="text-base font-bold text-slate-900">{activeReport.title}</h2>
                      <Badge variant={activeReport.status as any}>{activeReport.status.toUpperCase()}</Badge>
                    </div>
                    <p className="text-[11px] text-slate-500 font-mono">
                      Generated on {content.metadata?.generated_at || 'Recently'} by {activeReport.creator_name}
                    </p>
                  </div>

                  {/* Controls: Mode Toggle, Approval, PDF Export */}
                  <div className="flex items-center gap-2">
                    {/* View Mode Toggle */}
                    <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs">
                      <button
                        onClick={() => setViewMode('incoming_member_view')}
                        className={`px-2.5 py-1 rounded font-medium transition-all ${
                          viewMode === 'incoming_member_view'
                            ? 'bg-white text-slate-900 shadow-xs'
                            : 'text-slate-500 hover:text-slate-900'
                        }`}
                      >
                        Incoming Member View
                      </button>
                      <button
                        onClick={() => setViewMode('pm_view')}
                        className={`px-2.5 py-1 rounded font-medium transition-all ${
                          viewMode === 'pm_view'
                            ? 'bg-white text-slate-900 shadow-xs'
                            : 'text-slate-500 hover:text-slate-900'
                        }`}
                      >
                        PM Audit View
                      </button>
                    </div>

                    <button
                      onClick={() => handleDownloadPdf(activeReport.id)}
                      className="px-3 py-1.5 bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" />
                      PDF
                    </button>

                    {activeReport.status !== 'approved' && (
                      <button
                        onClick={handleApprove}
                        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors shadow-xs"
                      >
                        <Check className="w-3.5 h-3.5" />
                        Approve
                      </button>
                    )}

                    {activeReport.status !== 'rejected' && (
                      <button
                        onClick={handleReject}
                        className="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        Reject
                      </button>
                    )}
                  </div>
                </div>

                {/* 14 Sections Render */}
                <div className="space-y-6 text-xs text-slate-800">
                  {/* 1. Project Overview */}
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <h3 className="font-bold text-slate-900 mb-1.5 text-xs uppercase tracking-wider text-teal-800">
                      {content['1_project_overview']?.title || '1. Project Overview'}
                    </h3>
                    <p className="leading-relaxed text-slate-700">
                      {content['1_project_overview']?.purpose || 'N/A'}
                    </p>
                    <div className="mt-2 text-[11px] font-semibold text-slate-600">
                      Stage: {content['1_project_overview']?.stage || 'Active Handover'}
                    </div>
                  </div>

                  {/* 2. Objectives */}
                  <div>
                    <h3 className="font-bold text-slate-900 mb-2 uppercase tracking-wider text-teal-800">
                      {content['2_project_objectives']?.title || '2. Project Objectives'}
                    </h3>
                    <ul className="space-y-1 pl-1">
                      {(content['2_project_objectives']?.objectives || []).map((obj: string, i: number) => (
                        <li key={i} className="flex items-center gap-2 text-slate-700">
                          <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                          <span>{obj}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* 3. Team Responsibilities */}
                  <div>
                    <h3 className="font-bold text-slate-900 mb-2 uppercase tracking-wider text-teal-800">
                      {content['3_team_responsibilities']?.title || '3. Team Responsibilities'}
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      {(content['3_team_responsibilities']?.roles || []).map((r: any, i: number) => (
                        <div key={i} className="p-3 bg-white rounded-lg border border-slate-200">
                          <div className="font-bold text-slate-900">{r.role}</div>
                          <div className="text-[11px] text-teal-700 font-medium mb-1">{r.name}</div>
                          <div className="text-[11px] text-slate-500 leading-tight">{r.responsibility}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 4. Completed Work & 5. Ongoing Work */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-emerald-50/40 rounded-lg border border-emerald-100">
                      <h3 className="font-bold text-emerald-900 mb-2 uppercase tracking-wider">
                        {content['4_completed_work']?.title || '4. Completed Work'}
                      </h3>
                      <div className="space-y-2">
                        {(content['4_completed_work']?.items || []).map((item: any, i: number) => (
                          <div key={i} className="text-[11px] text-slate-700">
                            • <span className="font-semibold text-slate-900">{item.title}</span> — {item.description}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="p-4 bg-amber-50/40 rounded-lg border border-amber-100">
                      <h3 className="font-bold text-amber-900 mb-2 uppercase tracking-wider">
                        {content['5_ongoing_work']?.title || '5. Ongoing Work'}
                      </h3>
                      <div className="space-y-2">
                        {(content['5_ongoing_work']?.items || []).map((item: any, i: number) => (
                          <div key={i} className="text-[11px] text-slate-700">
                            • <span className="font-semibold text-slate-900">{item.title}</span> ({item.priority})
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* 6. Pending Tasks & 7. Decisions */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h3 className="font-bold text-slate-900 mb-2 uppercase tracking-wider text-teal-800">
                        {content['6_pending_tasks']?.title || '6. Pending Continuation Tasks'}
                      </h3>
                      <div className="space-y-2">
                        {(content['6_pending_tasks']?.items || []).map((item: any, i: number) => (
                          <div key={i} className="p-2.5 bg-slate-50 rounded border border-slate-200">
                            <span className="font-semibold text-slate-900">{item.title}</span>
                            <div className="text-[11px] text-slate-500 mt-0.5">{item.description}</div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h3 className="font-bold text-slate-900 mb-2 uppercase tracking-wider text-teal-800">
                        {content['7_important_decisions']?.title || '7. Architecture Decisions'}
                      </h3>
                      <div className="space-y-2">
                        {(content['7_important_decisions']?.items || []).map((item: any, i: number) => (
                          <div key={i} className="p-2.5 bg-slate-50 rounded border border-slate-200">
                            <span className="font-semibold text-slate-900">{item.title}</span>
                            <div className="text-[11px] text-slate-600 mt-0.5">{item.reasoning}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* 8. Technical Architecture Summary */}
                  <div className="p-4 bg-slate-900 text-white rounded-lg">
                    <h3 className="font-bold text-teal-400 mb-1.5 uppercase tracking-wider">
                      {content['8_technical_architecture']?.title || '8. Architecture Summary'}
                    </h3>
                    <p className="text-[11px] text-slate-300 leading-relaxed font-mono">
                      {content['8_technical_architecture']?.stack_summary}
                    </p>
                  </div>

                  {/* 9. Risks and Blockers & 10. Dependencies */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-rose-50/40 rounded-lg border border-rose-200">
                      <h3 className="font-bold text-rose-900 mb-2 uppercase tracking-wider">
                        {content['9_risks_and_blockers']?.title || '9. Risks & Blockers'}
                      </h3>
                      <div className="space-y-2">
                        {(content['9_risks_and_blockers']?.items || []).map((r: any, i: number) => (
                          <div key={i} className="text-[11px] text-rose-900">
                            • <span className="font-semibold">{r.title}</span>: {r.description}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="p-4 bg-sky-50/40 rounded-lg border border-sky-200">
                      <h3 className="font-bold text-sky-900 mb-2 uppercase tracking-wider">
                        {content['10_dependencies']?.title || '10. Task Dependencies'}
                      </h3>
                      <div className="space-y-2">
                        {(content['10_dependencies']?.items || []).map((d: any, i: number) => (
                          <div key={i} className="text-[11px] text-sky-900">
                            • <span className="font-semibold">{d.source}</span> → depends on <span className="font-semibold">{d.target}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* 11. Unresolved Questions */}
                  <div>
                    <h3 className="font-bold text-slate-900 mb-2 uppercase tracking-wider text-teal-800">
                      {content['11_unresolved_questions']?.title || '11. Unresolved Questions & Contradictions'}
                    </h3>
                    <div className="space-y-1.5">
                      {(content['11_unresolved_questions']?.items || []).map((q: any, i: number) => (
                        <div key={i} className="p-2.5 bg-amber-50 rounded border border-amber-200 text-amber-900 text-[11px]">
                          • <span className="font-semibold">{q.question || q}</span>: {q.details || 'Identified in source notes'}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 12. Recommended Next Actions (Continuity Blueprint) */}
                  <div className="p-4 bg-gradient-to-r from-teal-50 to-cyan-50 rounded-lg border border-teal-200">
                    <h3 className="font-bold text-teal-900 mb-2 uppercase tracking-wider">
                      {content['12_recommended_next_actions']?.title || '12. Continuity Blueprint Next Steps'}
                    </h3>
                    <div className="space-y-1.5">
                      {(content['12_recommended_next_actions']?.items || []).map((action: string, i: number) => (
                        <div key={i} className="flex items-center gap-2 text-teal-950 font-medium text-[11px]">
                          <span className="w-4 h-4 rounded-full bg-teal-600 text-white text-[10px] flex items-center justify-center font-bold">
                            {i + 1}
                          </span>
                          <span>{action}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 13. Supporting Evidence Passport */}
                  <div>
                    <h3 className="font-bold text-slate-900 mb-2 uppercase tracking-wider text-teal-800">
                      {content['13_supporting_evidence']?.title || '13. Supporting Evidence Passport'}
                    </h3>
                    <div className="space-y-2">
                      {(content['13_supporting_evidence']?.items || []).slice(0, 5).map((ev: any, i: number) => (
                        <div key={i} className="p-2.5 bg-slate-50 rounded border border-slate-200 text-[11px]">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-semibold text-slate-900">{ev.claim}</span>
                            <Badge variant={ev.status?.toLowerCase() as any}>{ev.status}</Badge>
                          </div>
                          <div className="text-slate-500 font-mono italic text-[10px]">
                            "{ev.snippet}" — {ev.document} (P.{ev.page || 1})
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 14. Source Document Registry */}
                  <div>
                    <h3 className="font-bold text-slate-900 mb-2 uppercase tracking-wider text-teal-800">
                      {content['14_source_documents']?.title || '14. Source Documents'}
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {(content['14_source_documents']?.documents || []).map((doc: any, i: number) => (
                        <span key={i} className="px-3 py-1 bg-slate-100 rounded-lg text-[11px] font-mono text-slate-700 border border-slate-200">
                          {doc.filename} ({doc.type})
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

