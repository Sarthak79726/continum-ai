import React, { useState, useEffect } from 'react';
import {
  GitBranch,
  FileText,
  Layers,
  RefreshCw,
  Plus,
  CheckCircle2,
  Clock,
  ExternalLink,
  ShieldCheck,
  Cpu,
  Database
} from 'lucide-react';
import { projectApi, sourceApi } from '../services/api';
import { Project, SourceConnection } from '../types';

export const SourceIntegrationsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [sources, setSources] = useState<SourceConnection[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Connect Modal
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [repoOwner, setRepoOwner] = useState('continuum-ai');
  const [repoName, setRepoName] = useState('smart-campus-core');
  const [repoBranch, setRepoBranch] = useState('main');
  const [githubToken, setGithubToken] = useState('');

  useEffect(() => {
    projectApi.list().then((projs) => {
      setProjects(projs);
      if (projs.length > 0) setSelectedProjectId(projs[0].id);
    }).catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedProjectId) return;
    loadSources(selectedProjectId);
  }, [selectedProjectId]);

  const loadSources = async (projId: number) => {
    try {
      setIsLoading(true);
      const res = await sourceApi.listByProject(projId);
      setSources(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSyncGitHub = async () => {
    if (!selectedProjectId) return;
    try {
      setIsSyncing(true);
      await sourceApi.syncGitHub(selectedProjectId);
      setStatusMessage('GitHub repository synchronized successfully!');
      loadSources(selectedProjectId);
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err) {
      console.error(err);
      setStatusMessage('Sync failed.');
    } finally {
      setIsSyncing(false);
    }
  };

  const handleConnectGitHub = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjectId) return;
    try {
      await sourceApi.connectGitHub(selectedProjectId, {
        owner: repoOwner,
        repo: repoName,
        branch: repoBranch,
        token: githubToken || undefined
      });
      setShowConnectModal(false);
      setStatusMessage(`Connected GitHub repository: ${repoOwner}/${repoName}`);
      loadSources(selectedProjectId);
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err) {
      console.error(err);
      setStatusMessage('Failed to connect repository.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-500/10 text-teal-400 border border-teal-500/30">
              Multi-Source Ingestion
            </span>
            <span className="text-xs text-slate-400 font-mono">Continuous Institutional Synchronization</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-1 flex items-center gap-2">
            <GitBranch className="w-7 h-7 text-teal-400" />
            Source Repository & Knowledge Connectors
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Connect code repositories, issue trackers, and document hubs to extract evidence and reconstruct engineer contributions.
          </p>
        </div>

        {/* Project Selector & Connect Button */}
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
          <button
            onClick={() => setShowConnectModal(true)}
            className="px-3.5 py-2 bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold rounded-xl flex items-center gap-1.5 transition-all shadow-xs"
          >
            <Plus className="w-4 h-4" />
            Connect Source
          </button>
        </div>
      </div>

      {statusMessage && (
        <div className="p-3 bg-teal-500/10 border border-teal-500/40 rounded-xl text-teal-300 text-xs flex items-center justify-between">
          <span>{statusMessage}</span>
          <button onClick={() => setStatusMessage(null)} className="text-teal-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Primary Connectors Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {/* GitHub Card */}
        {sources.length > 0 ? (
          sources.map((src) => (
            <div key={src.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 hover:border-slate-700 transition-all shadow-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-teal-400">
                    <GitBranch className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">{src.connection_name}</h3>
                    <span className="text-[11px] text-slate-400 font-mono">Branch: {src.branch}</span>
                  </div>
                </div>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold uppercase ${
                  src.sync_status === 'synced' || src.sync_status === 'synthetic_demo'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : 'bg-amber-500/20 text-amber-300'
                }`}>
                  {src.sync_status}
                </span>
              </div>

              <div className="text-xs font-mono text-slate-400 bg-slate-950 p-2.5 rounded-lg border border-slate-800/80 break-all">
                {src.repository_url || 'https://github.com/continuum-ai/smart-campus-core'}
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 bg-slate-950/60 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-bold block">Commits Synced</span>
                  <span className="text-sm font-bold text-white mt-0.5 block">
                    {src.metadata_json?.commits_synced || 8}
                  </span>
                </div>
                <div className="p-2 bg-slate-950/60 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-bold block">PRs Indexed</span>
                  <span className="text-sm font-bold text-purple-300 mt-0.5 block">
                    {src.metadata_json?.prs_synced || 3}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-slate-800 text-[11px] text-slate-400">
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  {src.last_synced_at ? new Date(src.last_synced_at).toLocaleTimeString() : 'Just now'}
                </span>
                <button
                  onClick={handleSyncGitHub}
                  disabled={isSyncing}
                  className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-teal-300 rounded-lg font-semibold flex items-center gap-1 disabled:opacity-50 transition-colors"
                >
                  <RefreshCw className={`w-3 h-3 ${isSyncing ? 'animate-spin' : ''}`} />
                  {isSyncing ? 'Syncing...' : 'Sync Now'}
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center gap-3">
              <GitBranch className="w-8 h-8 text-teal-400" />
              <div>
                <h4 className="text-xs font-bold text-white">GitHub Repository</h4>
                <p className="text-[11px] text-slate-400">Sync commits, branches, and PRs</p>
              </div>
            </div>
            <button
              onClick={() => setShowConnectModal(true)}
              className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-teal-300 rounded-lg text-xs font-semibold"
            >
              Connect GitHub Repository
            </button>
          </div>
        )}

        {/* Verified Documents Hub */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 hover:border-slate-700 transition-all shadow-xs">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-teal-400">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Project Document Vault</h3>
                <span className="text-[11px] text-slate-400 font-mono">PDF, DOCX, CSV, TXT</span>
              </div>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase">
              Active
            </span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            4 certified project specifications and architecture RFCs ingested, chunked, and embedded into the local vector database.
          </p>

          <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800 text-xs flex items-center justify-between text-slate-300">
            <span>Vector Embeddings:</span>
            <span className="font-mono text-teal-400 font-bold">all-MiniLM-L6-v2 (384-dim)</span>
          </div>

          <div className="pt-3 border-t border-slate-800 flex justify-end">
            <a
              href="/documents"
              className="text-xs text-teal-400 hover:text-teal-300 font-semibold flex items-center gap-1"
            >
              Manage Documents <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>

        {/* Jira / Sprint Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 hover:border-slate-700 transition-all shadow-xs">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-sky-400">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Sprint & Issue Tracker</h3>
                <span className="text-[11px] text-slate-400 font-mono">Jira / Linear Bridge</span>
              </div>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full font-mono font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30 uppercase">
              Linked
            </span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Tracks issue lifecycle tickets (e.g. CAMPUS-101, CAMPUS-102) and maps resolution evidence to git commits.
          </p>

          <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800 text-xs flex items-center justify-between text-slate-300">
            <span>Active Sprint:</span>
            <span className="font-mono text-sky-400 font-bold">Sprint 24 — Auth & Attendance</span>
          </div>

          <div className="pt-3 border-t border-slate-800 flex justify-end">
            <span className="text-xs text-slate-500">Live Auto-Sync</span>
          </div>
        </div>
      </div>

      {/* Connect Modal */}
      {showConnectModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-teal-400" />
              Connect GitHub Repository
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Continuum AI will index commit history, pull request discussions, and code diffs to attribute institutional knowledge.
            </p>

            <form onSubmit={handleConnectGitHub} className="mt-4 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-slate-300">Repo Owner</label>
                  <input
                    type="text"
                    value={repoOwner}
                    onChange={(e) => setRepoOwner(e.target.value)}
                    required
                    className="w-full mt-1.5 bg-slate-800 text-slate-200 text-xs p-2.5 rounded-lg border border-slate-700"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-300">Repository Name</label>
                  <input
                    type="text"
                    value={repoName}
                    onChange={(e) => setRepoName(e.target.value)}
                    required
                    className="w-full mt-1.5 bg-slate-800 text-slate-200 text-xs p-2.5 rounded-lg border border-slate-700"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300">Default Branch</label>
                <input
                  type="text"
                  value={repoBranch}
                  onChange={(e) => setRepoBranch(e.target.value)}
                  className="w-full mt-1.5 bg-slate-800 text-slate-200 text-xs p-2.5 rounded-lg border border-slate-700"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300">
                  GitHub Personal Access Token <span className="text-slate-500">(Optional for Public Repos)</span>
                </label>
                <input
                  type="password"
                  value={githubToken}
                  onChange={(e) => setGithubToken(e.target.value)}
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                  className="w-full mt-1.5 bg-slate-800 text-slate-200 text-xs p-2.5 rounded-lg border border-slate-700"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowConnectModal(false)}
                  className="px-4 py-2 text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold rounded-lg shadow-sm"
                >
                  Connect & Synchronize
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
