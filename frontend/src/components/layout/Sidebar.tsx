import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderGit2,
  FileText,
  Network,
  ShieldCheck,
  ListTodo,
  FileCheck2,
  Users2,
  Settings,
  Sparkles,
  Trash2,
  CheckCircle2,
  Layers
} from 'lucide-react';
import { demoApi } from '../../services/api';

export const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [demoNotice, setDemoNotice] = useState<string | null>(null);

  const navItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Projects', path: '/projects', icon: FolderGit2 },
    { label: 'Documents', path: '/documents', icon: FileText },
    { label: 'Knowledge Graph', path: '/graph', icon: Network },
    { label: 'Evidence Passport', path: '/evidence', icon: ShieldCheck },
    { label: 'Continuity Blueprint', path: '/tasks', icon: ListTodo },
    { label: 'Handover Reports', path: '/handovers', icon: FileCheck2 },
    { label: 'Review Centre', path: '/reviews', icon: CheckCircle2 },
    { label: 'Team & Access', path: '/team', icon: Users2 },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];

  const handleLoadDemo = async () => {
    try {
      setLoadingDemo(true);
      const res = await demoApi.loadDemo();
      setDemoNotice('Demo loaded!');
      setTimeout(() => setDemoNotice(null), 3000);
      navigate(`/projects/${res.project_id}`);
      window.location.reload();
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDemo(false);
    }
  };

  const handlePurgeDemo = async () => {
    if (!window.confirm('Remove synthetic demonstration project from your workspace?')) return;
    try {
      await demoApi.purgeDemo();
      setDemoNotice('Demo removed');
      setTimeout(() => setDemoNotice(null), 3000);
      navigate('/projects');
      window.location.reload();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 h-screen sticky top-0 border-r border-slate-800 z-40">
      {/* Brand Header */}
      <div className="h-14 px-6 flex items-center gap-3 border-b border-slate-800">
        <div className="w-8 h-8 rounded-lg bg-teal-500 text-slate-950 flex items-center justify-center font-black text-sm shadow-sm shadow-teal-500/20">
          C
        </div>
        <div className="flex flex-col">
          <span className="font-bold text-white text-sm tracking-tight leading-none">Continuum AI</span>
          <span className="text-[10px] text-teal-400 font-medium tracking-wider uppercase mt-1">Knowledge Continuity</span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
          Platform Workspace
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-teal-500/10 text-teal-300 border border-teal-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Demo Dataset Controls */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/40">
        <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] font-semibold text-slate-200 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-teal-400" />
              Demo Dataset
            </span>
            {demoNotice && <span className="text-[10px] text-teal-400 font-mono">{demoNotice}</span>}
          </div>
          <p className="text-[10px] text-slate-400 leading-tight mb-2.5">
            Smart Campus System with departing developer Rahul & 4 verified documents.
          </p>
          <div className="flex items-center gap-1.5">
            <button
              onClick={handleLoadDemo}
              disabled={loadingDemo}
              className="flex-1 py-1 px-2 bg-teal-600 hover:bg-teal-500 text-white rounded text-[11px] font-medium transition-colors flex items-center justify-center gap-1 shadow-xs disabled:opacity-50"
            >
              <Sparkles className="w-3 h-3" />
              {loadingDemo ? 'Loading...' : 'Load Demo'}
            </button>
            <button
              onClick={handlePurgeDemo}
              title="Purge Demo Data"
              className="p-1 text-slate-400 hover:text-rose-400 rounded hover:bg-slate-700/50 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
};

