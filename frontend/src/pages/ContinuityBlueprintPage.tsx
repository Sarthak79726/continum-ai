import React, { useEffect, useState } from 'react';
import {
  ListTodo,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Sparkles,
  Plus,
  ArrowRight,
  Filter,
  Search,
  CheckSquare
} from 'lucide-react';
import { projectApi, taskApi } from '../services/api';
import { Project, TaskItem } from '../types';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { EmptyState } from '../components/common/EmptyState';

export const ContinuityBlueprintPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Task creation/edit modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<TaskItem | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [statusVal, setStatusVal] = useState<'pending' | 'in_progress' | 'completed' | 'blocked'>('pending');
  const [priorityVal, setPriorityVal] = useState<'critical' | 'high' | 'medium' | 'low'>('medium');
  const [ownerVal, setOwnerVal] = useState('Incoming Member');

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      loadTasks(selectedProjectId);
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

  const loadTasks = async (projId: number) => {
    try {
      setLoading(true);
      const list = await taskApi.list(projId);
      setTasks(list);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenCreate = () => {
    setEditingTask(null);
    setTitle('');
    setDescription('');
    setStatusVal('pending');
    setPriorityVal('high');
    setOwnerVal('Incoming Member');
    setIsModalOpen(true);
  };

  const handleOpenEdit = (task: TaskItem) => {
    setEditingTask(task);
    setTitle(task.title);
    setDescription(task.description || '');
    setStatusVal(task.status);
    setPriorityVal(task.priority);
    setOwnerVal(task.owner);
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjectId || !title.trim()) return;

    try {
      if (editingTask) {
        const updated = await taskApi.update(editingTask.id, {
          title,
          description,
          status: statusVal,
          priority: priorityVal,
          owner: ownerVal,
        });
        setTasks(tasks.map((t) => (t.id === editingTask.id ? updated : t)));
      } else {
        const created = await taskApi.create(selectedProjectId, {
          title,
          description,
          status: statusVal,
          priority: priorityVal,
          owner: ownerVal,
          is_recommendation: false,
        });
        setTasks([...tasks, created]);
      }
      setIsModalOpen(false);
    } catch (err) {
      console.error(err);
    }
  };

  const handleToggleComplete = async (task: TaskItem) => {
    const nextStatus = task.status === 'completed' ? 'pending' : 'completed';
    try {
      const updated = await taskApi.update(task.id, { status: nextStatus });
      setTasks(tasks.map((t) => (t.id === task.id ? updated : t)));
    } catch (err) {
      console.error(err);
    }
  };

  // Split recommendations vs extracted facts
  const recommendations = tasks.filter((t) => t.is_recommendation);
  const regularTasks = tasks.filter((t) => !t.is_recommendation);

  const filteredTasks = regularTasks.filter((t) => {
    const matchesSearch =
      t.title.toLowerCase().includes(search.toLowerCase()) ||
      (t.description && t.description.toLowerCase().includes(search.toLowerCase())) ||
      t.owner.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || t.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Continuity Blueprint</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Signature Feature: Actionable continuation plan connecting incoming employees directly to project momentum.
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
              onClick={handleOpenCreate}
              className="px-3 py-1.5 bg-slate-900 text-white rounded-lg text-xs font-semibold flex items-center gap-1 shadow-xs hover:bg-slate-800"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Task
            </button>
          </div>
        )}
      </div>

      {/* Prioritized Recommended Continuation Sequence */}
      {recommendations.length > 0 && (
        <div className="bg-gradient-to-r from-teal-900 to-slate-900 text-white rounded-xl p-6 shadow-md border border-teal-800/50">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-teal-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-teal-300">
              Continuity Blueprint — Prioritized Next Action Sequence
            </h3>
          </div>
          <p className="text-xs text-slate-300 mb-4 leading-relaxed">
            AI-synthesized priority actions derived from missing credentials, active blockers, and handover meeting notes.
          </p>

          <div className="space-y-2.5">
            {recommendations.map((rec, idx) => (
              <div
                key={rec.id}
                className="bg-white/10 hover:bg-white/15 backdrop-blur-xs p-3 rounded-lg border border-white/10 flex items-center justify-between gap-3 text-xs"
              >
                <div className="flex items-center gap-3">
                  <span className="w-5 h-5 rounded-full bg-teal-400 text-slate-950 font-bold flex items-center justify-center text-[10px]">
                    {idx + 1}
                  </span>
                  <span className="font-semibold text-white">{rec.title}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="needs_review">Incoming Priority</Badge>
                  <button
                    onClick={() => handleToggleComplete(rec)}
                    className="p-1 hover:text-teal-300 text-slate-400"
                    title="Mark Done"
                  >
                    <CheckSquare className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search & Filter */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search tasks by title, owner, or description..."
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
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="blocked">Blocked</option>
          </select>
        </div>
      </div>

      {/* Task List Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Reconstructed Tasks & Workstreams ({filteredTasks.length})
          </h3>
          <span className="text-[11px] text-slate-500">Separated Facts & Evidence References</span>
        </div>

        {filteredTasks.length === 0 ? (
          <div className="text-center py-12 text-xs text-slate-400">
            No tasks match your search filter.
          </div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-medium border-b border-slate-100">
              <tr>
                <th className="px-5 py-3 w-10">Done</th>
                <th className="px-4 py-3">Task Title & Description</th>
                <th className="px-4 py-3">Owner</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Evidence Source</th>
                <th className="px-4 py-3 text-right">Edit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredTasks.map((t) => (
                <tr key={t.id} className="hover:bg-slate-50/50">
                  <td className="px-5 py-3.5">
                    <button
                      onClick={() => handleToggleComplete(t)}
                      className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${
                        t.status === 'completed'
                          ? 'bg-emerald-500 border-emerald-500 text-white'
                          : 'border-slate-300 hover:border-teal-500'
                      }`}
                    >
                      {t.status === 'completed' && <CheckCircle2 className="w-3.5 h-3.5" />}
                    </button>
                  </td>
                  <td className="px-4 py-3.5 font-semibold text-slate-900 max-w-sm">
                    <div>{t.title}</div>
                    {t.description && (
                      <div className="text-[11px] font-normal text-slate-500 mt-0.5 line-clamp-1">
                        {t.description}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3.5 text-slate-700 whitespace-nowrap font-medium">
                    {t.owner}
                  </td>
                  <td className="px-4 py-3.5 whitespace-nowrap">
                    <Badge variant={t.priority as any}>{t.priority.toUpperCase()}</Badge>
                  </td>
                  <td className="px-4 py-3.5 whitespace-nowrap">
                    <Badge variant={t.status as any}>{t.status.replace('_', ' ').toUpperCase()}</Badge>
                  </td>
                  <td className="px-4 py-3.5 text-slate-500 text-[11px] whitespace-nowrap">
                    {t.source_reference || 'Extracted Knowledge'}
                  </td>
                  <td className="px-4 py-3.5 text-right whitespace-nowrap">
                    <button
                      onClick={() => handleOpenEdit(t)}
                      className="px-2 py-1 text-slate-500 hover:text-slate-900 rounded hover:bg-slate-100 font-medium"
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Task Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingTask ? 'Edit Task' : 'Add Continuity Task'}
      >
        <form onSubmit={handleSave} className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Title *</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Description</label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
            />
          </div>
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Status</label>
              <select
                value={statusVal}
                onChange={(e) => setStatusVal(e.target.value as any)}
                className="w-full px-2 py-1.5 text-xs border border-slate-300 rounded-lg"
              >
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="blocked">Blocked</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Priority</label>
              <select
                value={priorityVal}
                onChange={(e) => setPriorityVal(e.target.value as any)}
                className="w-full px-2 py-1.5 text-xs border border-slate-300 rounded-lg"
              >
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Owner</label>
              <input
                type="text"
                value={ownerVal}
                onChange={(e) => setOwnerVal(e.target.value)}
                className="w-full px-2 py-1.5 text-xs border border-slate-300 rounded-lg"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-3">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-1.5 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg"
            >
              {editingTask ? 'Update Task' : 'Create Task'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

