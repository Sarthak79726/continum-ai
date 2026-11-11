import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Send,
  ShieldCheck,
  AlertTriangle,
  FileText,
  GitCommit,
  GitPullRequest,
  Code2,
  Database,
  ArrowRight,
  HelpCircle,
  RefreshCw,
  Layers,
  UserCheck
} from 'lucide-react';
import { projectApi, employeeApi, askAiApi } from '../services/api';
import { Project, EmployeeProfile, AskAIResponse, AskCitation } from '../types';

interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text?: string;
  response?: AskAIResponse;
  timestamp: string;
}

export const AskProjectAIPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [employees, setEmployees] = useState<EmployeeProfile[]>([]);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | ''>('');
  const [roleScope, setRoleScope] = useState<string>('BACKEND');

  const [inputQuery, setInputQuery] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  const sampleQuestions = [
    'Why is token blacklist failing in the auth service?',
    'What APIs did Rahul build and what is still incomplete?',
    'What database migrations were added in the last sprint?',
    'What are the active blockers and unresolved bugs?',
    'Where is the Redis configuration defined and why does it disconnect?'
  ];

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
      const rahul = emps.find((e) => e.name.toLowerCase().includes('rahul'));
      if (rahul) setSelectedEmployeeId(rahul.id);
    }).catch(console.error);
  }, [selectedProjectId]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isAsking]);

  const handleSend = async (queryText?: string) => {
    const q = (queryText || inputQuery).trim();
    if (!q || !selectedProjectId) return;

    const userMsg: ChatMessage = {
      id: Math.random().toString(),
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsAsking(true);

    try {
      const res = await askAiApi.ask({
        project_id: selectedProjectId,
        question: q,
        employee_id: selectedEmployeeId ? Number(selectedEmployeeId) : undefined,
        role_scope: roleScope
      });

      const aiMsg: ChatMessage = {
        id: Math.random().toString(),
        sender: 'ai',
        response: res,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.error(err);
      const errorMsg: ChatMessage = {
        id: Math.random().toString(),
        sender: 'ai',
        text: 'Error contacting Project AI engine. Please verify the backend is running.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsAsking(false);
    }
  };

  const getCitationIcon = (type: string) => {
    switch (type.toUpperCase()) {
      case 'CODE_COMMIT':
        return <GitCommit className="w-3.5 h-3.5 text-teal-400" />;
      case 'PULL_REQUEST':
        return <GitPullRequest className="w-3.5 h-3.5 text-purple-400" />;
      case 'API_SPEC':
        return <Code2 className="w-3.5 h-3.5 text-sky-400" />;
      case 'DATABASE_SCHEMA':
        return <Database className="w-3.5 h-3.5 text-amber-400" />;
      case 'DOCUMENT':
      default:
        return <FileText className="w-3.5 h-3.5 text-emerald-400" />;
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)]">
      {/* Header & Controls Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shrink-0 mb-4 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-500/10 text-teal-400 border border-teal-500/30">
                Grounded Continuity RAG
              </span>
              <span className="text-xs text-slate-400 font-mono">Zero Hallucination Tolerance</span>
            </div>
            <h1 className="text-xl font-bold text-white tracking-tight mt-1 flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-teal-400" />
              Ask Your Project AI
            </h1>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-3">
            <div>
              <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Project</label>
              <select
                value={selectedProjectId || ''}
                onChange={(e) => setSelectedProjectId(Number(e.target.value))}
                className="bg-slate-800 text-slate-200 text-xs px-3 py-1.5 rounded-lg border border-slate-700"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Employee Scope</label>
              <select
                value={selectedEmployeeId}
                onChange={(e) => setSelectedEmployeeId(e.target.value ? Number(e.target.value) : '')}
                className="bg-slate-800 text-slate-200 text-xs px-3 py-1.5 rounded-lg border border-slate-700"
              >
                <option value="">All Contributors</option>
                {employees.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.name} ({e.role_title.split(' ')[0]})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Role Perspective</label>
              <div className="flex items-center bg-slate-800 p-0.5 rounded-lg border border-slate-700 text-xs">
                {['BACKEND', 'FRONTEND', 'PRODUCT', 'ALL'].map((role) => (
                  <button
                    key={role}
                    onClick={() => setRoleScope(role)}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all ${
                      roleScope === role ? 'bg-teal-600 text-white shadow-xs' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    {role}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Messages Viewport */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 bg-slate-900/50 border border-slate-800/80 rounded-2xl">
            <div className="w-14 h-14 rounded-2xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400 mb-4">
              <Sparkles className="w-7 h-7" />
            </div>
            <h2 className="text-lg font-bold text-white">Ask Anything About The Handover</h2>
            <p className="text-xs text-slate-400 max-w-md mt-1 leading-relaxed">
              Every answer is synthesized directly from authorized Git commits, PRs, technical specs, and architecture decisions with exact citations.
            </p>

            {/* Quick Prompt Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-6 max-w-2xl w-full text-left">
              {sampleQuestions.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(q)}
                  className="p-3 bg-slate-800/80 hover:bg-slate-800 text-slate-300 hover:text-white rounded-xl border border-slate-700/80 hover:border-teal-500/50 text-xs transition-all flex items-center justify-between group"
                >
                  <span className="truncate mr-2 font-medium">{q}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-teal-400 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'} animate-fadeIn`}
            >
              {msg.sender === 'user' ? (
                <div className="max-w-2xl bg-teal-600 text-white rounded-2xl rounded-tr-xs px-4 py-3 shadow-md text-xs font-medium">
                  {msg.text}
                  <div className="text-[10px] text-teal-200 mt-1 text-right">{msg.timestamp}</div>
                </div>
              ) : (
                <div className="max-w-3xl w-full bg-slate-900 border border-slate-800 rounded-2xl rounded-tl-xs p-5 shadow-xs space-y-4">
                  {/* AI Message Header */}
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-lg bg-teal-500/20 text-teal-400 flex items-center justify-center">
                        <Sparkles className="w-3.5 h-3.5" />
                      </div>
                      <span className="text-xs font-bold text-white">Continuity AI Answer</span>
                    </div>

                    {msg.response && (
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold uppercase ${
                        msg.response.confidence === 'HIGH' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                        msg.response.confidence === 'MEDIUM' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                        'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                      }`}>
                        {msg.response.confidence} Confidence
                      </span>
                    )}
                  </div>

                  {/* Main Answer Body */}
                  <div className="text-xs text-slate-200 leading-relaxed space-y-2 whitespace-pre-wrap">
                    {msg.response ? msg.response.answer : msg.text}
                  </div>

                  {/* Citations Box */}
                  {msg.response && msg.response.citations && msg.response.citations.length > 0 && (
                    <div className="pt-3 border-t border-slate-800">
                      <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <ShieldCheck className="w-3.5 h-3.5 text-teal-400" />
                        Evidence Citations ({msg.response.citations.length})
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {msg.response.citations.map((c, ci) => (
                          <div key={ci} className="p-2.5 bg-slate-950/70 border border-slate-800/80 rounded-lg text-xs">
                            <div className="flex items-center gap-1.5 font-semibold text-slate-200">
                              {getCitationIcon(c.source_type)}
                              <span className="truncate">{c.title}</span>
                            </div>
                            <div className="text-[10px] font-mono text-teal-400 mt-1">Ref: {c.reference}</div>
                            {c.quote_snippet && (
                              <p className="text-[11px] text-slate-400 mt-1 italic line-clamp-2">"{c.quote_snippet}"</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Missing Evidence / Contradiction Warnings */}
                  {msg.response?.missing_evidence_notice && (
                    <div className="p-3 bg-amber-950/30 border border-amber-800/40 rounded-xl text-xs text-amber-300 flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                      <div>
                        <strong>Notice: </strong>
                        {msg.response.missing_evidence_notice}
                      </div>
                    </div>
                  )}

                  {msg.response?.contradictions_noted && (
                    <div className="p-3 bg-rose-950/30 border border-rose-800/40 rounded-xl text-xs text-rose-300 flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                      <div>
                        <strong>Contradiction Detected: </strong>
                        {msg.response.contradictions_noted}
                      </div>
                    </div>
                  )}

                  {/* Follow-up Prompts */}
                  {msg.response && msg.response.recommended_follow_ups && msg.response.recommended_follow_ups.length > 0 && (
                    <div className="pt-2 flex flex-wrap gap-1.5 items-center">
                      <span className="text-[10px] text-slate-500 font-bold uppercase mr-1">Suggested Next:</span>
                      {msg.response.recommended_follow_ups.map((f, fi) => (
                        <button
                          key={fi}
                          onClick={() => handleSend(f)}
                          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-teal-300 hover:text-white rounded-lg text-[11px] font-medium border border-slate-700 transition-colors"
                        >
                          {f}
                        </button>
                      ))}
                    </div>
                  )}

                  <div className="text-[10px] text-slate-500 text-right">{msg.timestamp}</div>
                </div>
              )}
            </div>
          ))
        )}

        {isAsking && (
          <div className="flex items-center gap-2 p-4 bg-slate-900 border border-slate-800 rounded-2xl w-64 animate-pulse">
            <Sparkles className="w-4 h-4 text-teal-400 animate-spin" />
            <span className="text-xs text-slate-300">Searching commits & evidence...</span>
          </div>
        )}
        <div ref={chatBottomRef} />
      </div>

      {/* Query Input Bar */}
      <div className="pt-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-2xl p-2 focus-within:border-teal-500 shadow-lg"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask about architecture, commits, unresolved bugs, or why a decision was made..."
            className="flex-1 bg-transparent px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-hidden"
          />
          <button
            type="submit"
            disabled={isAsking || !inputQuery.trim()}
            className="p-2.5 bg-teal-600 hover:bg-teal-500 text-white rounded-xl disabled:opacity-50 transition-colors shadow-xs"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};

