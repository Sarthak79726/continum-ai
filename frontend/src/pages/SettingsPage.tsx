import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Settings,
  Cpu,
  Database,
  Shield,
  Key,
  LogOut,
  Sparkles,
  Info,
  Server
} from 'lucide-react';
import { settingsApi } from '../services/api';
import { Badge } from '../components/common/Badge';

export const SettingsPage: React.FC = () => {
  const { user, logout } = useAuth();
  const [statusData, setStatusData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await settingsApi.getStatus();
      setStatusData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">System Settings & Telemetry</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Workspace profile, configurable AI provider status, and vector database persistence.
        </p>
      </div>

      {/* User Profile Card */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Shield className="w-4 h-4 text-teal-600" />
          Active User Profile
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div>
            <span className="text-slate-500 text-[11px]">Full Name</span>
            <div className="font-semibold text-slate-900 mt-0.5">{user?.name}</div>
          </div>
          <div>
            <span className="text-slate-500 text-[11px]">Work Email</span>
            <div className="font-semibold text-slate-900 mt-0.5 font-mono">{user?.email}</div>
          </div>
          <div>
            <span className="text-slate-500 text-[11px]">Security Tier</span>
            <div className="mt-0.5">
              <Badge variant="completed">{user?.role}</Badge>
            </div>
          </div>
        </div>
      </div>

      {/* AI Provider Telemetry */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-600" />
          Configurable AI Provider Engine
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs mb-4">
          <div>
            <span className="text-slate-500 text-[11px]">Configured Provider</span>
            <div className="font-bold text-slate-900 uppercase mt-0.5">
              {statusData?.ai_engine?.provider || 'demo'}
            </div>
          </div>
          <div>
            <span className="text-slate-500 text-[11px]">Inference Model</span>
            <div className="font-semibold text-slate-800 font-mono mt-0.5">
              {statusData?.ai_engine?.model || 'gemini-1.5-flash'}
            </div>
          </div>
          <div>
            <span className="text-slate-500 text-[11px]">Execution Engine</span>
            <div className="mt-0.5">
              <Badge variant={statusData?.ai_engine?.is_api_key_configured ? 'verified' : 'needs_review'}>
                {statusData?.ai_engine?.mode || 'Deterministic Local Engine'}
              </Badge>
            </div>
          </div>
        </div>

        <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-[11px] text-slate-600 space-y-1">
          <div className="flex items-center gap-1 font-semibold text-slate-800">
            <Info className="w-3.5 h-3.5 text-teal-600" />
            Zero-Cost Demonstration Guarantee
          </div>
          <p className="leading-relaxed">
            Continuum AI does not require paid API keys to run or evaluate. If no external key is supplied in the `.env` file, the high-precision Deterministic Local NLP Extractor parses real document structures, extracts grounded citations, and links the Evidence Passport natively.
          </p>
        </div>
      </div>

      {/* Vector Database & Storage */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Database className="w-4 h-4 text-indigo-600" />
          Database & Vector Storage
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-slate-500 text-[11px]">Relational Persistence</span>
            <div className="font-semibold text-slate-800 font-mono mt-0.5">
              {statusData?.storage?.database || 'SQLite (SQLAlchemy Engine)'}
            </div>
          </div>
          <div>
            <span className="text-slate-500 text-[11px]">Semantic Vector Store</span>
            <div className="font-semibold text-slate-800 font-mono mt-0.5">
              {statusData?.storage?.vector_store || 'ChromaDB Persistent Collections'}
            </div>
          </div>
          <div>
            <span className="text-slate-500 text-[11px]">Chroma Storage Path</span>
            <div className="font-mono text-slate-600 text-[11px] mt-0.5">
              {statusData?.storage?.vector_dir || './chroma_data'}
            </div>
          </div>
          <div>
            <span className="text-slate-500 text-[11px]">Document Upload Directory</span>
            <div className="font-mono text-slate-600 text-[11px] mt-0.5">
              {statusData?.storage?.upload_dir || './uploads'}
            </div>
          </div>
        </div>
      </div>

      {/* Security & Sign Out */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between">
        <div>
          <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">End Active Session</h4>
          <p className="text-xs text-slate-500 mt-0.5">
            Sign out of Continuum AI workspace on this workstation.
          </p>
        </div>
        <button
          onClick={logout}
          className="px-4 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          Sign Out
        </button>
      </div>
    </div>
  );
};

