import React, { useEffect, useState } from 'react';
import {
  Users2,
  UserPlus,
  ShieldCheck,
  Trash2,
  Mail,
  Shield,
  CheckCircle2,
  KeyRound
} from 'lucide-react';
import { projectApi, teamApi } from '../services/api';
import { Project, ProjectMember } from '../types';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { EmptyState } from '../components/common/EmptyState';

export const TeamPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [loading, setLoading] = useState(true);

  // Add member modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('TEAM_MEMBER');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      loadMembers(selectedProjectId);
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

  const loadMembers = async (projId: number) => {
    try {
      setLoading(true);
      const data = await teamApi.listMembers(projId);
      setMembers(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjectId || !email.trim()) return;

    setError(null);
    setSubmitting(true);
    try {
      const added = await teamApi.addMember(selectedProjectId, { email, role });
      setMembers([...members, added]);
      setIsModalOpen(false);
      setEmail('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add member to project.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemoveMember = async (userId: number) => {
    if (!selectedProjectId) return;
    if (!window.confirm('Remove this member from the project workspace?')) return;
    try {
      await teamApi.removeMember(selectedProjectId, userId);
      setMembers(members.filter((m) => m.user_id !== userId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to remove member.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Team & Access Governance</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Role-Based Access Control (RBAC) enforced by backend API permissions.
          </p>
        </div>

        {projects.length > 0 && (
          <div className="flex items-center gap-3">
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
            <button
              onClick={() => { setError(null); setIsModalOpen(true); }}
              className="px-3 py-1.5 bg-slate-900 text-white rounded-lg text-xs font-semibold flex items-center gap-1 shadow-xs hover:bg-slate-800"
            >
              <UserPlus className="w-3.5 h-3.5" />
              Add Member
            </button>
          </div>
        )}
      </div>

      {/* Role Definitions Card */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center gap-1.5 font-bold text-slate-900 text-xs mb-1">
            <Shield className="w-3.5 h-3.5 text-teal-600" /> ADMIN
          </div>
          <p className="text-[11px] text-slate-500 leading-tight">
            Full global visibility across all project repositories, audit trails, and system settings.
          </p>
        </div>
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center gap-1.5 font-bold text-slate-900 text-xs mb-1">
            <ShieldCheck className="w-3.5 h-3.5 text-sky-600" /> PROJECT MANAGER
          </div>
          <p className="text-[11px] text-slate-500 leading-tight">
            Can trigger AI reconstruction, edit tasks, generate dossiers, and officially approve/reject reports.
          </p>
        </div>
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center gap-1.5 font-bold text-slate-900 text-xs mb-1">
            <Users2 className="w-3.5 h-3.5 text-indigo-600" /> TEAM MEMBER
          </div>
          <p className="text-[11px] text-slate-500 leading-tight">
            Can upload project documents, inspect evidence passport, and update personal tasks.
          </p>
        </div>
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center gap-1.5 font-bold text-slate-900 text-xs mb-1">
            <KeyRound className="w-3.5 h-3.5 text-emerald-600" /> INCOMING MEMBER
          </div>
          <p className="text-[11px] text-slate-500 leading-tight">
            Tailored continuation access: receives Continuity Blueprint next actions and technical ramp-up context.
          </p>
        </div>
      </div>

      {/* Members Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Workspace Members ({members.length})
          </h3>
          <span className="text-[11px] text-slate-500 font-mono">Backend Enforced</span>
        </div>

        {loading ? (
          <div className="text-center py-12 text-xs text-slate-500 font-mono animate-pulse">
            Loading team permissions...
          </div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-medium border-b border-slate-100">
              <tr>
                <th className="px-5 py-3">Member Name</th>
                <th className="px-4 py-3">Email Address</th>
                <th className="px-4 py-3">Role Tier</th>
                <th className="px-4 py-3">Joined Date</th>
                <th className="px-4 py-3 text-right">Remove</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {members.map((m) => (
                <tr key={m.id} className="hover:bg-slate-50/50">
                  <td className="px-5 py-3.5 font-semibold text-slate-900 flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-slate-900 text-white flex items-center justify-center text-[10px] font-bold">
                      {m.name.charAt(0).toUpperCase()}
                    </div>
                    <span>{m.name}</span>
                  </td>
                  <td className="px-4 py-3.5 text-slate-600 font-mono text-[11px]">
                    {m.email}
                  </td>
                  <td className="px-4 py-3.5">
                    <Badge variant={m.role === 'PROJECT_MANAGER' || m.role === 'ADMIN' ? 'completed' : 'default'}>
                      {m.role}
                    </Badge>
                  </td>
                  <td className="px-4 py-3.5 text-slate-500">
                    {new Date(m.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    {m.id !== 0 && (
                      <button
                        onClick={() => handleRemoveMember(m.user_id)}
                        className="p-1 text-slate-400 hover:text-rose-600 rounded hover:bg-slate-100"
                        title="Remove member"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Add Member Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add Project Team Member"
      >
        <form onSubmit={handleAddMember} className="space-y-4">
          {error && (
            <div className="p-2.5 bg-rose-50 text-rose-700 text-xs rounded-lg border border-rose-200">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              User Email Address *
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="colleague@campus.edu"
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Project Access Role
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg"
            >
              <option value="PROJECT_MANAGER">Project Manager (Can Approve Handovers)</option>
              <option value="TEAM_MEMBER">Team Member (Engineer / Contributor)</option>
              <option value="INCOMING_MEMBER">Incoming Member (Continuity Handover Recipient)</option>
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-lg text-xs disabled:opacity-50"
            >
              {submitting ? 'Adding...' : 'Grant Access'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

