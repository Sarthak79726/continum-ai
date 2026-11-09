import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FolderGit2,
  Plus,
  Search,
  Filter,
  MoreVertical,
  Trash2,
  Edit,
  ExternalLink,
  FileText,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { projectApi } from '../services/api';
import { Project } from '../types';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { EmptyState } from '../components/common/EmptyState';

export const ProjectsPage: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [projStatus, setProjStatus] = useState('active');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const data = await projectApi.list();
      setProjects(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenCreate = () => {
    setEditingProject(null);
    setName('');
    setDescription('');
    setProjStatus('active');
    setIsModalOpen(true);
  };

  const handleOpenEdit = (p: Project, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingProject(p);
    setName(p.name);
    setDescription(p.description || '');
    setProjStatus(p.status);
    setIsModalOpen(true);
  };

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Delete this project and its document vector store?')) return;
    try {
      await projectApi.delete(id);
      setProjects(projects.filter((p) => p.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    try {
      setSubmitting(true);
      if (editingProject) {
        const updated = await projectApi.update(editingProject.id, {
          name,
          description,
          status: projStatus,
        });
        setProjects(projects.map((p) => (p.id === editingProject.id ? updated : p)));
      } else {
        const created = await projectApi.create({
          name,
          description,
          status: projStatus,
        });
        setProjects([created, ...projects]);
      }
      setIsModalOpen(false);
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const filteredProjects = projects.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      (p.description && p.description.toLowerCase().includes(search.toLowerCase()));
    const matchesStatus = statusFilter === 'all' || p.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Project Management</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Create, manage and inspect continuous knowledge workspaces.
          </p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="px-3.5 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg shadow-xs flex items-center gap-1.5 transition-colors self-start"
        >
          <Plus className="w-3.5 h-3.5" />
          Create Project
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search projects by title or description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500 text-slate-700"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active</option>
            <option value="completed">Completed</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="text-center py-12 text-xs text-slate-500 font-mono animate-pulse">
          Loading project telemetry...
        </div>
      ) : filteredProjects.length === 0 ? (
        <EmptyState
          icon={FolderGit2}
          title="No projects match your filter"
          description="Adjust your search query or create a new project to start document extraction."
          actionText="Create Project"
          onAction={handleOpenCreate}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredProjects.map((p) => (
            <div
              key={p.id}
              onClick={() => navigate(`/projects/${p.id}`)}
              className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs hover:shadow-md hover:border-teal-500/50 cursor-pointer transition-all flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="text-sm font-semibold text-slate-900 group-hover:text-teal-600 transition-colors">
                    {p.name}
                  </h3>
                  <div className="flex items-center gap-1.5 shrink-0">
                    {p.is_demo && <Badge variant="needs_review">DEMO DATA</Badge>}
                    <Badge variant={p.status === 'active' ? 'completed' : 'default'}>
                      {p.status}
                    </Badge>
                  </div>
                </div>
                <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed mb-4">
                  {p.description || 'No project description provided.'}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1" title="Documents">
                    <FileText className="w-3.5 h-3.5 text-slate-400" />
                    {p.document_count}
                  </span>
                  <span className="flex items-center gap-1" title="Tasks">
                    <CheckCircle2 className="w-3.5 h-3.5 text-slate-400" />
                    {p.task_count}
                  </span>
                  <span className="flex items-center gap-1" title="Risks">
                    <AlertTriangle className="w-3.5 h-3.5 text-slate-400" />
                    {p.risk_count}
                  </span>
                </div>
                <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={(e) => handleOpenEdit(p, e)}
                    className="p-1 text-slate-400 hover:text-slate-600 rounded hover:bg-slate-100"
                    title="Edit project"
                  >
                    <Edit className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={(e) => handleDelete(p.id, e)}
                    className="p-1 text-slate-400 hover:text-rose-600 rounded hover:bg-slate-100"
                    title="Delete project"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Project Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingProject ? 'Edit Project' : 'Create New Project'}
      >
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Project Name *</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Smart Campus Management System"
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Description</label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the scope, objectives, or current stage of this project..."
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Status</label>
            <select
              value={projStatus}
              onChange={(e) => setProjStatus(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
            >
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="archived">Archived</option>
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-3.5 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-1.5 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors disabled:opacity-50"
            >
              {submitting ? 'Saving...' : editingProject ? 'Update Project' : 'Create Project'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

