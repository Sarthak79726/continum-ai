import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FolderGit2,
  FileText,
  CheckCircle,
  Clock,
  AlertTriangle,
  FileCheck2,
  ArrowUpRight,
  Sparkles,
  Layers,
  Plus
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts';
import { analyticsApi, demoApi } from '../services/api';
import { DashboardStats } from '../types';
import { Badge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingDemo, setLoadingDemo] = useState(false);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await analyticsApi.getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load dashboard stats', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadDemo = async () => {
    try {
      setLoadingDemo(true);
      await demoApi.loadDemo();
      await fetchStats();
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDemo(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-xs text-slate-500 font-mono animate-pulse">Loading dashboard telemetry...</div>
      </div>
    );
  }

  const isWorkspaceEmpty = !stats || stats.total_projects === 0;

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Mission Control</h1>
            <span className="px-2 py-0.5 text-[10px] font-semibold bg-teal-50 text-teal-700 border border-teal-200 rounded-full">
              Enterprise Continuity
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
            Continuum AI connects authorized documents, reconstructs technical history, links verified evidence, and protects institutional memory during team transitions.
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => navigate('/projects')}
            className="px-3.5 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg shadow-xs flex items-center gap-1.5 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            New Project
          </button>
          {isWorkspaceEmpty && (
            <button
              onClick={handleLoadDemo}
              disabled={loadingDemo}
              className="px-3.5 py-2 text-xs font-semibold text-teal-800 bg-teal-50 hover:bg-teal-100 border border-teal-200 rounded-lg shadow-xs flex items-center gap-1.5 transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5 text-teal-600" />
              {loadingDemo ? 'Initializing...' : 'Load Smart Campus Demo'}
            </button>
          )}
        </div>
      </div>

      {isWorkspaceEmpty ? (
        <EmptyState
          icon={Layers}
          title="No projects in this workspace yet"
          description="Initialize your first project to ingest PDF, DOCX, CSV or TXT documents, or explore the pre-packaged Smart Campus Management System dataset."
          actionText="Create New Project"
          onAction={() => navigate('/projects')}
          secondaryActionText="Load Sample Dataset"
          onSecondaryAction={handleLoadDemo}
        />
      ) : (
        <>
          {/* 6 Top Metric Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500">Projects</span>
                <FolderGit2 className="w-4 h-4 text-slate-400" />
              </div>
              <div className="text-2xl font-bold text-slate-900">{stats.total_projects}</div>
              <div className="text-[10px] text-teal-600 font-medium mt-1">Active workspaces</div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500">Documents</span>
                <FileText className="w-4 h-4 text-cyan-600" />
              </div>
              <div className="text-2xl font-bold text-slate-900">{stats.documents_processed}</div>
              <div className="text-[10px] text-cyan-600 font-medium mt-1">Indexed in ChromaDB</div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500">Completed</span>
                <CheckCircle className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="text-2xl font-bold text-slate-900">{stats.completed_tasks}</div>
              <div className="text-[10px] text-emerald-600 font-medium mt-1">Verified milestones</div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500">Pending</span>
                <Clock className="w-4 h-4 text-amber-500" />
              </div>
              <div className="text-2xl font-bold text-slate-900">{stats.pending_tasks}</div>
              <div className="text-[10px] text-amber-600 font-medium mt-1">Backlog continuation</div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500">Risks</span>
                <AlertTriangle className="w-4 h-4 text-rose-500" />
              </div>
              <div className="text-2xl font-bold text-slate-900">{stats.identified_risks}</div>
              <div className="text-[10px] text-rose-600 font-medium mt-1">Identified blockers</div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500">Handovers</span>
                <FileCheck2 className="w-4 h-4 text-indigo-500" />
              </div>
              <div className="text-2xl font-bold text-slate-900">{stats.handover_reports}</div>
              <div className="text-[10px] text-indigo-600 font-medium mt-1">
                {stats.pending_reviews > 0 ? `${stats.pending_reviews} pending review` : 'All approved'}
              </div>
            </div>
          </div>

          {/* Analytics Visualizations */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Task Breakdown Pie Chart */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Continuity Task Distribution
                </h3>
                <span className="text-[11px] text-slate-500">Live Breakdown</span>
              </div>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={stats.task_completion_distribution}
                      innerRadius={60}
                      outerRadius={85}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {stats.task_completion_distribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '11px' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex items-center justify-center gap-6 mt-2 text-xs">
                {stats.task_completion_distribution.map((item) => (
                  <div key={item.name} className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-slate-600 font-medium">{item.name} ({item.value})</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Risk Severity Bar Chart */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Risk & Blocker Severity Assessment
                </h3>
                <span className="text-[11px] text-slate-500">Extracted from Sources</span>
              </div>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.risk_severity_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <XAxis dataKey="severity" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '11px' }} />
                    <Bar dataKey="count" fill="#0d9488" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="text-center text-[11px] text-slate-500 mt-2">
                Severity classified through structured epistemic reasoning
              </div>
            </div>
          </div>

          {/* Operational Tables Section */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Recent Projects */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs lg:col-span-1">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Recent Workspaces</h3>
                <button
                  onClick={() => navigate('/projects')}
                  className="text-xs text-teal-600 hover:text-teal-700 font-medium flex items-center gap-0.5"
                >
                  View all <ArrowUpRight className="w-3 h-3" />
                </button>
              </div>
              <div className="space-y-2.5">
                {stats.recent_projects.map((p) => (
                  <div
                    key={p.id}
                    onClick={() => navigate(`/projects/${p.id}`)}
                    className="p-3 rounded-lg border border-slate-100 hover:border-slate-200 hover:bg-slate-50/50 cursor-pointer transition-all"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-slate-900 truncate max-w-[170px]">{p.name}</span>
                      {p.is_demo && <Badge variant="needs_review">DEMO DATA</Badge>}
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-slate-500">
                      <span>{p.doc_count} docs</span>
                      <span>•</span>
                      <span>{p.task_count} tasks</span>
                      <span>•</span>
                      <span>{p.created_at}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Pending Handover Reviews */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs lg:col-span-1">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Pending Reviews</h3>
                <button
                  onClick={() => navigate('/reviews')}
                  className="text-xs text-teal-600 hover:text-teal-700 font-medium flex items-center gap-0.5"
                >
                  Review Centre <ArrowUpRight className="w-3 h-3" />
                </button>
              </div>
              {stats.pending_review_reports.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-400">
                  No reports awaiting reviewer approval.
                </div>
              ) : (
                <div className="space-y-2.5">
                  {stats.pending_review_reports.map((r) => (
                    <div
                      key={r.id}
                      onClick={() => navigate('/reviews')}
                      className="p-3 rounded-lg border border-amber-100 bg-amber-50/30 hover:bg-amber-50 cursor-pointer transition-all"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-semibold text-slate-900 truncate">{r.title}</span>
                        <Badge variant="needs_review">Needs Review</Badge>
                      </div>
                      <div className="text-[11px] text-slate-500 flex items-center justify-between">
                        <span>{r.project_name}</span>
                        <span>{r.created_at}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Recent Audit Timeline */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs lg:col-span-1">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Audit Log & Activity</h3>
                <span className="text-[10px] text-slate-400 font-mono">Immutable</span>
              </div>
              <div className="space-y-2.5">
                {stats.activity_timeline.map((act) => (
                  <div key={act.id} className="text-xs border-l-2 border-teal-500 pl-3 py-0.5">
                    <div className="font-semibold text-slate-800 leading-tight">{act.action}</div>
                    <div className="text-[11px] text-slate-500 truncate">{act.details}</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">{act.created_at}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

