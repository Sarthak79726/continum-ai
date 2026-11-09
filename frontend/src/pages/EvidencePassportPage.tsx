import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  Search,
  Filter,
  FileText,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  ExternalLink,
  Edit2
} from 'lucide-react';
import { projectApi, evidenceApi } from '../services/api';
import { Project, EvidenceItem } from '../types';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { EmptyState } from '../components/common/EmptyState';

export const EvidencePassportPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Inspection & verification edit modal
  const [selectedItem, setSelectedItem] = useState<EvidenceItem | null>(null);
  const [editStatus, setEditStatus] = useState<string>('VERIFIED');
  const [editQuality, setEditQuality] = useState<string>('Direct Citation');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      loadEvidence(selectedProjectId);
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

  const loadEvidence = async (projId: number) => {
    try {
      setLoading(true);
      const list = await evidenceApi.list(projId);
      setEvidenceList(list);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenInspect = (item: EvidenceItem) => {
    setSelectedItem(item);
    setEditStatus(item.verification_status);
    setEditQuality(item.quality_label);
  };

  const handleSaveVerification = async () => {
    if (!selectedItem) return;
    try {
      setSaving(true);
      const updated = await evidenceApi.updateStatus(selectedItem.id, {
        verification_status: editStatus,
        quality_label: editQuality,
      });
      setEvidenceList(evidenceList.map((e) => (e.id === updated.id ? updated : e)));
      setSelectedItem(null);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const filteredItems = evidenceList.filter((item) => {
    const matchesSearch =
      item.claim_text.toLowerCase().includes(search.toLowerCase()) ||
      item.source_snippet.toLowerCase().includes(search.toLowerCase()) ||
      item.document_name.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || item.verification_status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Evidence Passport</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Signature Feature: Grounded epistemic verification linking every AI claim to its source text snippet.
          </p>
        </div>

        {projects.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-slate-600">Active Project:</span>
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
          </div>
        )}
      </div>

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search claims, quotes, or document sources..."
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
            <option value="all">All Verification Statuses</option>
            <option value="VERIFIED">Verified (Direct Source)</option>
            <option value="NEEDS_REVIEW">Needs Review</option>
            <option value="CONFLICTING">Conflicting Discrepancy</option>
            <option value="UNVERIFIED">Unverified Claim</option>
          </select>
        </div>
      </div>

      {/* Evidence Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Verified Claim Dossier ({filteredItems.length})
          </h3>
          <span className="text-[11px] text-teal-600 font-medium">Epistemically Audited</span>
        </div>

        {filteredItems.length === 0 ? (
          <div className="text-center py-12 text-xs text-slate-400">
            No claims match your filter. Re-run analysis or adjust search term.
          </div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-medium border-b border-slate-100">
              <tr>
                <th className="px-5 py-3">Extracted Claim Description</th>
                <th className="px-4 py-3">Supporting Source</th>
                <th className="px-4 py-3">Direct Grounded Quote Snippet</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Evidence Quality</th>
                <th className="px-4 py-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredItems.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50/50">
                  <td className="px-5 py-3.5 font-semibold text-slate-900 max-w-xs">
                    {item.claim_text}
                  </td>
                  <td className="px-4 py-3.5 text-slate-600 whitespace-nowrap">
                    <div className="flex items-center gap-1.5 font-medium">
                      <FileText className="w-3.5 h-3.5 text-slate-400" />
                      <span>{item.document_name}</span>
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono">
                      Page {item.page_number || 1}
                    </div>
                  </td>
                  <td className="px-4 py-3.5 text-slate-600 max-w-md font-mono text-[11px]">
                    <div className="line-clamp-2 bg-slate-50 p-1.5 rounded border border-slate-100 italic">
                      "{item.source_snippet}"
                    </div>
                  </td>
                  <td className="px-4 py-3.5 whitespace-nowrap">
                    <Badge variant={item.verification_status.toLowerCase() as any}>
                      {item.verification_status.replace('_', ' ')}
                    </Badge>
                  </td>
                  <td className="px-4 py-3.5 whitespace-nowrap">
                    <span className="text-[11px] font-medium text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                      {item.quality_label}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-right whitespace-nowrap">
                    <button
                      onClick={() => handleOpenInspect(item)}
                      className="px-2.5 py-1 text-xs font-semibold text-teal-700 hover:text-teal-800 bg-teal-50 hover:bg-teal-100 rounded border border-teal-200 transition-colors"
                    >
                      Audit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Inspection & Human Audit Modal */}
      <Modal
        isOpen={!!selectedItem}
        onClose={() => setSelectedItem(null)}
        title="Evidence Passport — Source Audit & Verification"
        maxWidth="xl"
      >
        {selectedItem && (
          <div className="space-y-4 text-xs">
            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                Claim Under Review
              </span>
              <p className="text-sm font-semibold text-slate-900 mt-0.5">
                {selectedItem.claim_text}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
              <div>
                <span className="text-[10px] text-slate-500">Document Source:</span>
                <div className="font-semibold text-slate-800">{selectedItem.document_name}</div>
              </div>
              <div>
                <span className="text-[10px] text-slate-500">Page Reference:</span>
                <div className="font-semibold text-slate-800">Page {selectedItem.page_number || 1}</div>
              </div>
            </div>

            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                Direct Source Citation Snippet
              </span>
              <div className="p-3 bg-slate-950 text-slate-200 rounded-lg border border-slate-800 font-mono text-xs leading-relaxed mt-1">
                "{selectedItem.source_snippet}"
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100 grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Human Verification Status
                </label>
                <select
                  value={editStatus}
                  onChange={(e) => setEditStatus(e.target.value)}
                  className="w-full px-2.5 py-1.5 border border-slate-300 rounded-lg text-xs"
                >
                  <option value="VERIFIED">VERIFIED</option>
                  <option value="NEEDS_REVIEW">NEEDS_REVIEW</option>
                  <option value="CONFLICTING">CONFLICTING</option>
                  <option value="UNVERIFIED">UNVERIFIED</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Evidence Quality Label
                </label>
                <select
                  value={editQuality}
                  onChange={(e) => setEditQuality(e.target.value)}
                  className="w-full px-2.5 py-1.5 border border-slate-300 rounded-lg text-xs"
                >
                  <option value="Direct Citation">Direct Citation</option>
                  <option value="Inferred">Inferred</option>
                  <option value="Conflicting">Conflicting</option>
                  <option value="Insufficient Context">Insufficient Context</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setSelectedItem(null)}
                className="px-3 py-1.5 text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveVerification}
                disabled={saving}
                className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-lg shadow-xs disabled:opacity-50"
              >
                {saving ? 'Updating...' : 'Save Audit Decision'}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

