import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Eye, EyeOff, Lock, Mail, User, Sparkles, ArrowRight, AlertCircle, CheckCircle2, RefreshCw } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, register, loginDemo } = useAuth();
  
  const [isSignUp, setIsSignUp] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('TEAM_MEMBER');

  const checkBackend = async () => {
    setBackendStatus('checking');
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        setBackendStatus('online');
      } else {
        setBackendStatus('offline');
      }
    } catch {
      setBackendStatus('offline');
    }
  };

  useEffect(() => {
    checkBackend();
  }, []);

  const extractErrorMessage = (err: any): string => {
    if (err.response?.data?.detail) {
      if (typeof err.response.data.detail === 'string') {
        return err.response.data.detail;
      }
      return JSON.stringify(err.response.data.detail);
    }
    if (
      !err.response ||
      err.code === 'ERR_NETWORK' ||
      err.code === 'ECONNABORTED' ||
      err.response?.status === 500 ||
      err.response?.status === 502 ||
      err.response?.status === 503 ||
      err.response?.status === 504 ||
      (typeof err.response?.data === 'string' && err.response.data.includes('ECONNREFUSED'))
    ) {
      return 'Backend API is offline or unreachable at http://127.0.0.1:8000. Please launch the backend server using start.bat or terminal.';
    }
    return err.message || 'Authentication failed. Please verify your credentials.';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isSignUp) {
        if (!name.trim()) throw new Error('Full name is required.');
        await register(name, email, password, role);
      } else {
        await login(email, password);
      }
      navigate('/');
    } catch (err: any) {
      setError(extractErrorMessage(err));
      checkBackend();
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError(null);
    setIsSignUp(false);
    setEmail('demo@continuum.ai');
    setPassword('password123');
    setLoading(true);

    try {
      await loginDemo();
      navigate('/');
    } catch (err: any) {
      setError(extractErrorMessage(err));
      checkBackend();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Brand logo & header */}
      <div className="text-center mb-6 relative z-10">
        <div className="w-12 h-12 rounded-xl bg-teal-500 text-slate-950 flex items-center justify-center font-black text-xl mx-auto mb-3 shadow-lg shadow-teal-500/20">
          C
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Continuum AI</h1>
        <p className="text-xs text-slate-400 mt-1 max-w-sm">
          Intelligent Knowledge Handover & Project Continuity Platform
        </p>

        {/* Backend health status badge */}
        <div className="mt-3">
          {backendStatus === 'online' && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Backend Connected (Port 8000)
            </span>
          )}
          {backendStatus === 'offline' && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20 shadow-xs">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              Backend Offline (Port 8000)
              <button
                type="button"
                onClick={checkBackend}
                className="ml-1 text-slate-400 hover:text-white"
                title="Retry checking backend"
              >
                <RefreshCw className="w-3 h-3" />
              </button>
            </span>
          )}
          {backendStatus === 'checking' && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium bg-slate-800 text-slate-400 border border-slate-700 shadow-xs">
              <RefreshCw className="w-3 h-3 animate-spin text-teal-400" />
              Checking Backend...
            </span>
          )}
        </div>
      </div>

      {/* Auth Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl w-full max-w-md p-8 relative z-10">
        {/* Backend Offline banner if detected */}
        {backendStatus === 'offline' && (
          <div className="mb-5 p-3.5 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-200 text-xs space-y-2">
            <div className="flex items-center gap-2 font-semibold text-amber-300">
              <AlertCircle className="w-4 h-4 shrink-0 text-amber-400" />
              <span>Backend Server is Not Running</span>
            </div>
            <p className="text-[11px] text-amber-200/90 leading-relaxed">
              Login requires the FastAPI backend on port 8000. Launch it with <strong className="text-white">start.bat</strong> or run in your terminal:
            </p>
            <div className="bg-slate-950 p-2 rounded text-[11px] font-mono text-teal-300 select-all border border-slate-800 break-all">
              python -m uvicorn app.main:app --app-dir ./backend --reload --port 8000
            </div>
          </div>
        )}

        {/* Mode Toggle */}
        <div className="flex p-1 bg-slate-950 rounded-lg mb-6 border border-slate-800">
          <button
            type="button"
            onClick={() => { setIsSignUp(false); setError(null); }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all ${
              !isSignUp ? 'bg-slate-800 text-white shadow-xs' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setIsSignUp(true); setError(null); }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all ${
              isSignUp ? 'bg-slate-800 text-white shadow-xs' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Create Account
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
            <span className="leading-relaxed">{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {isSignUp && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Rahul Sharma"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-teal-500"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Work Email</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="demo@continuum.ai"
                className="w-full pl-9 pr-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-teal-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-10 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-teal-500"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="p-1 text-slate-500 hover:text-slate-300 absolute right-2.5 top-1/2 -translate-y-1/2"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {isSignUp && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Project Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-teal-500"
              >
                <option value="PROJECT_MANAGER">Project Manager</option>
                <option value="TEAM_MEMBER">Team Member (Developer)</option>
                <option value="INCOMING_MEMBER">Incoming Member (Successor)</option>
                <option value="ADMIN">System Administrator</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold rounded-lg text-xs transition-colors flex items-center justify-center gap-1.5 shadow-md shadow-teal-500/10 disabled:opacity-50 mt-2 cursor-pointer"
          >
            {loading ? 'Authenticating...' : isSignUp ? 'Create Continuum Account' : 'Sign In to Workspace'}
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* Safe Demo Login Shortcut */}
        <div className="mt-6 pt-6 border-t border-slate-800 text-center">
          <p className="text-[11px] text-slate-400 mb-2.5">Evaluating for hackathon or demo?</p>
          <button
            type="button"
            onClick={handleDemoLogin}
            disabled={loading}
            className="w-full py-2 px-3 bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700/80 rounded-lg text-xs font-medium transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-xs hover:border-teal-500/40"
          >
            <Sparkles className="w-3.5 h-3.5 text-teal-400" />
            1-Click Demo Login (demo@continuum.ai)
          </button>
        </div>
      </div>

      <div className="mt-6 text-center text-slate-500 text-[11px]">
        Continuum AI • Epistemic Traceability & Knowledge Grounding Engine
      </div>
    </div>
  );
};
