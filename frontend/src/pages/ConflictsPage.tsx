import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  GitCommit,
  FileText,
  ShieldAlert,
  ArrowRight,
  Filter,
  Layers,
  Sparkles
} from 'lucide-react';
import { projectApi, conflictApi } from '../services/api';
import { Project, ConflictItem } from '../types';

export const ConflictsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);
  const [filterStatus, setFilterStatus] = useState<'all' | 'open' | 'resolved'>('all');
  const [isLoading, setIsLoading] = useState(false);

  // Resolve Modal
  const [resolvingConflict, setResolvingConflict] = useState<ConflictItem | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    projectApi.list().then((projs) => {
      setProjects(projs);
      if (projs.length > 0) setSelectedProjectId(projs[0].id);
    }).catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedProjectId) return;
    loadConflicts(selectedProjectId);
  }, [selectedProjectId]);

  const loadConflicts = async (projId: number) => {
    try {
      setIsLoading(true);
      const res = await conflictApi.listByProject(projId);
      setConflicts(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resolvingConflict || !selectedProjectId) return;
    try {
      setIsSubmitting(true);
      await conflictApi.resolve(resolvingConflict.id, {
        resolution_notes: resolutionNotes
      });
      setResolvingConflict(null);
      setResolutionNotes('');
      loadConflicts(selectedProjectId);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const filtered = conflicts.filter((c) => {
    if (filterStatus === 'open') return c.resolution_status === 'open';
    if (filterStatus === 'resolved') return c.resolution_status === 'resolved';
    return true;
  });

  const openCount = conflicts.filter((c) => c.resolution_status === 'open').length;
  const resolvedCount = conflicts.filter((c) => c.resolution_status === 'resolved').length;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
              Contradiction Intelligence
            </span>
            <span className="text-xs text-slate-400 font-mono">Documentation vs Code Integrity</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-1 flex items-center gap-2">
            <ShieldAlert className="w-7 h-7 text-rose-400" />
            Artifact & Code Contradiction Radar
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Detects when PRD documents, tickets, or status updates conflict with true commit history and runtime test reality.
          </p>
        </div>

        {/* Project Selector & Filter */}
        <div className="flex items-center gap-3">
          <select
            value={selectedProjectId || ''}
            onChange={(e) => setSelectedProjectId(Number(e.target.value))}
            className="bg-slate-800 text-slate-200 text-xs px-3 py-2 rounded-lg border border-slate-700"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center justify-between">
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-bold">Total Contradictions</div>
            <div className="text-xl font-bold text-white mt-1">{conflicts.length}</div>
          </div>
          <AlertTriangle className="w-6 h-6 text-slate-600" />
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center justify-between">
          <div>
            <div className="text-[10px] text-amber-400 uppercase font-bold">Open Conflicts</div>
            <div className="text-xl font-bold text-amber-300 mt-1">{openCount}</div>
          </div>
          <div className="w-3 h-3 rounded-full bg-amber-400 animate-ping" />
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center justify-between">
          <div>
            <div className="text-[10px] text-emerald-400 uppercase font-bold">Resolved by Lead</div>
            <div className="text-xl font-bold text-emerald-300 mt-1">{resolvedCount}</div>
          </div>
          <CheckCircle2 className="w-6 h-6 text-emerald-500/50" />
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        {(['all', 'open', 'resolved'] as const).map((st) => (
          <button
            key={st}
            onClick={() => setFilterStatus(st)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all capitalize ${
              filterStatus === st
                ? 'bg-teal-600 text-white shadow-xs'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            {st} ({st === 'all' ? conflicts.length : st === 'open' ? openCount : resolvedCount})
          </button>
        ))}
      </div>

      {/* Conflicts List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="py-12 text-center text-slate-500">
            <div className="inline-block w-5 h-5 border-2 border-teal-500 border-t-transparent rounded-full animate-spin mb-2" />
            <p className="text-xs">Scanning artifacts and code commits for contradictions...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-slate-500 bg-slate-900 border border-slate-800 rounded-2xl">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-50" />
            <p className="text-xs">No contradictions found for current filter.</p>
          </div>
        ) : (
          filtered.map((c) => (
            <div key={c.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                    c.resolution_status === 'resolved'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : 'bg-rose-500/20 text-rose-300 border border-rose-500/30 animate-pulse'
                  }`}>
                    {c.resolution_status}
                  </span>
                  <h3 className="text-sm font-bold text-white">{c.title}</h3>
                </div>
                <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                  Type: {c.conflict_type}
                </span>
              </div>

              {/* Side by side comparison */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Statement A */}
                <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800/80 space-y-2">
                  <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase">
                    <span>Claim A (Document / Ticket)</span>
                    <span className="text-teal-400 font-mono truncate max-w-[150px]">{c.source_a}</span>
                  </div>
                  <p className="text-xs text-slate-200 leading-relaxed font-medium">"{c.statement_a}"</p>
                </div>

                {/* Statement B */}
                <div className="bg-rose-950/20 p-3.5 rounded-xl border border-rose-900/30 space-y-2">
                  <div className="flex items-center justify-between text-[10px] font-bold text-rose-400 uppercase">
                    <span>Contradicting Evidence (Code / Git)</span>
                    <span className="text-rose-300 font-mono truncate max-w-[150px]">{c.source_b}</span>
                  </div>
                  <p className="text-xs text-rose-100 leading-relaxed font-medium">"{c.statement_b}"</p>
                </div>
              </div>

              {/* Resolution Footer */}
              {c.resolution_status === 'resolved' ? (
                <div className="p-3 bg-emerald-950/20 border border-emerald-800/30 rounded-xl text-xs space-y-1">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold text-[10px] uppercase">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Resolved by {c.resolved_by || 'Technical Lead'}
                  </div>
                  <p className="text-slate-300 text-xs mt-1">{c.resolution_notes}</p>
                </div>
              ) : (
                <div className="flex justify-end pt-2 border-t border-slate-800">
                  <button
                    onClick={() => {
                      setResolvingConflict(c);
                      setResolutionNotes('');
                    }}
                    className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-teal-300 text-xs font-semibold rounded-lg border border-slate-700 flex items-center gap-1.5 transition-colors"
                  >
                    Resolve Contradiction
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Resolution Modal */}
      {resolvingConflict && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              Resolve Contradiction
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Provide authoritative technical justification clarifying the true state of the project.
            </p>

            <form onSubmit={handleResolve} className="mt-4 space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-300">Authoritative Resolution Note</label>
                <textarea
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  placeholder="e.g. Confirmed code reality: Redis cluster connectivity issue is still present. Re-opened CAMPUS-102 for Maya."
                  rows={4}
                  required
                  className="w-full mt-1.5 bg-slate-800 text-slate-200 text-xs p-3 rounded-lg border border-slate-700 focus:outline-hidden focus:border-teal-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setResolvingConflict(null)}
                  className="px-4 py-2 text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold rounded-lg shadow-sm"
                >
                  {isSubmitting ? 'Recording Resolution...' : 'Submit Resolution'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

