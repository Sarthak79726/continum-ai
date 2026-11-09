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
  Server,
  Save,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { settingsApi } from '../services/api';
import { Badge } from '../components/common/Badge';

export const SettingsPage: React.FC = () => {
  const { user, logout } = useAuth();
  const [statusData, setStatusData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Editable configuration
  const [provider, setProvider] = useState('demo');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('gemini-1.5-flash');
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await settingsApi.getStatus();
      setStatusData(data);
      if (data?.ai_engine) {
        setProvider(data.ai_engine.provider || 'demo');
        setModel(data.ai_engine.model || 'gemini-1.5-flash');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveSuccess(null);
    setSaveError(null);

    try {
      await settingsApi.update({
        ai_provider: provider,
        ai_api_key: apiKey,
        ai_model: model
      });
      setSaveSuccess('AI Engine settings updated successfully!');
      await loadSettings();
    } catch (err: any) {
      setSaveError(err.response?.data?.detail || err.message || 'Failed to update settings.');
    } finally {
      setSaving(false);
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

      {/* AI Provider Telemetry & Switcher */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-600" />
          Configurable AI Provider Engine
        </h3>

        {saveSuccess && (
          <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{saveSuccess}</span>
          </div>
        )}

        {saveError && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{saveError}</span>
          </div>
        )}

        <form onSubmit={handleSaveConfig} className="space-y-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">AI Provider</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500 font-medium"
              >
                <option value="demo">Deterministic Local / SentenceTransformers (Offline)</option>
                <option value="gemini">Google Gemini API (Live LLM)</option>
                <option value="openai">OpenAI API (Live LLM)</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">Inference Model</label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="gemini-1.5-flash / gpt-4o-mini"
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">API Key (Optional for Demo)</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={statusData?.ai_engine?.is_api_key_configured ? '••••••••••••••••' : 'Enter API Key (if live API)'}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500 font-mono"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white font-semibold rounded-lg text-xs flex items-center gap-1.5 transition-colors shadow-xs cursor-pointer"
            >
              <Save className="w-3.5 h-3.5" />
              {saving ? 'Updating...' : 'Save AI Configuration'}
            </button>
          </div>
        </form>

        <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-[11px] text-slate-600 space-y-1">
          <div className="flex items-center gap-1 font-semibold text-slate-800">
            <Info className="w-3.5 h-3.5 text-teal-600" />
            Zero-Cost Demonstration Guarantee
          </div>
          <p className="leading-relaxed">
            Continuum AI does not require paid API keys to run or evaluate. If no external key is supplied, the high-precision Deterministic Local NLP Extractor and local SentenceTransformers model parse real document structures, extract grounded citations, and link the Evidence Passport natively.
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
              {statusData?.storage?.database || 'SQLite (SQLAlchemy Engine with Foreign Keys)'}
            </div>
          </div>
          <div>
            <span className="text-slate-500 text-[11px]">Semantic Vector Store</span>
            <div className="font-semibold text-slate-800 font-mono mt-0.5">
              {statusData?.storage?.vector_store || 'ChromaDB (SentenceTransformers all-MiniLM-L6-v2)'}
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
          className="px-4 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
        >
          <LogOut className="w-3.5 h-3.5" />
          Sign Out
        </button>
      </div>
    </div>
  );
};
