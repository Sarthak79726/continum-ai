import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle2,
  XCircle,
  Clock,
  FileCheck2,
  Download,
  Eye,
  MessageSquare,
  ShieldCheck,
  Check
} from 'lucide-react';
import { reviewApi, handoverApi } from '../services/api';
import { HandoverReport } from '../types';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { EmptyState } from '../components/common/EmptyState';

export const ReviewCentrePage: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<{
    pending: HandoverReport[];
    approved: HandoverReport[];
    rejected: HandoverReport[];
    total_reviews: number;
  }>({
    pending: [],
    approved: [],
    rejected: [],
    total_reviews: 0,
  });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'pending' | 'approved' | 'rejected'>('pending');

  // Review modal
  const [reviewReport, setReviewReport] = useState<HandoverReport | null>(null);
  const [comments, setComments] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchReviews();
  }, []);

  const fetchReviews = async () => {
    try {
      setLoading(true);
      const res = await reviewApi.listReviews();
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (reportId: number) => {
    try {
      setSubmitting(true);
      await handoverApi.approve(reportId, comments || 'Verified and approved.');
      await fetchReviews();
      setReviewReport(null);
      setComments('');
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async (reportId: number) => {
    if (!comments.trim()) {
      alert('Please specify rejection feedback or required revisions in the comments field.');
      return;
    }
    try {
      setSubmitting(true);
      await handoverApi.reject(reportId, comments);
      await fetchReviews();
      setReviewReport(null);
      setComments('');
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDownloadPdf = async (reportId: number) => {
    try {
      const blob = await handoverApi.downloadPdf(reportId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Handover_Report_${reportId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      console.error(err);
    }
  };

  const currentList = data[activeTab] || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">Review Centre & Governance</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Authorized human sign-off portal. Handover dossiers require verified sign-off before official release.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 text-xs font-semibold">
        <button
          onClick={() => setActiveTab('pending')}
          className={`pb-3 px-4 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'pending'
              ? 'border-amber-500 text-amber-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Clock className="w-4 h-4 text-amber-500" />
          Pending Approvals ({data.pending.length})
        </button>
        <button
          onClick={() => setActiveTab('approved')}
          className={`pb-3 px-4 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'approved'
              ? 'border-emerald-500 text-emerald-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          Approved Reports ({data.approved.length})
        </button>
        <button
          onClick={() => setActiveTab('rejected')}
          className={`pb-3 px-4 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'rejected'
              ? 'border-rose-500 text-rose-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <XCircle className="w-4 h-4 text-rose-500" />
          Returned / Rejected ({data.rejected.length})
        </button>
      </div>

      {/* Reports List */}
      {loading ? (
        <div className="text-center py-12 text-xs text-slate-500 font-mono animate-pulse">
          Fetching review queue...
        </div>
      ) : currentList.length === 0 ? (
        <EmptyState
          icon={FileCheck2}
          title={`No ${activeTab} handover reports`}
          description="Reports submitted by project teams will appear here for governance review."
        />
      ) : (
        <div className="space-y-3">
          {currentList.map((r) => (
            <div
              key={r.id}
              className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-sm font-bold text-slate-900">{r.title}</h3>
                  <Badge variant={r.status as any}>{r.status.toUpperCase()}</Badge>
                  <span className="text-[10px] text-slate-400 font-mono">v{r.version}</span>
                </div>
                <div className="text-xs text-slate-500 flex items-center gap-3">
                  <span>Project: <strong className="text-slate-700">{r.project_name}</strong></span>
                  <span>•</span>
                  <span>Submitted by: {r.creator_name}</span>
                  <span>•</span>
                  <span>Date: {new Date(r.created_at).toLocaleDateString()}</span>
                </div>

                {r.reviews && r.reviews.length > 0 && (
                  <div className="mt-2.5 p-2 bg-slate-50 rounded-lg border border-slate-100 text-[11px] text-slate-600">
                    <span className="font-semibold text-slate-800">
                      Last Review ({r.reviews[0].reviewer_name}):
                    </span>{' '}
                    "{r.reviews[0].comments || r.reviews[0].action}"
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleDownloadPdf(r.id)}
                  className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  PDF
                </button>
                <button
                  onClick={() => setReviewReport(r)}
                  className="px-3.5 py-1.5 bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
                >
                  <Eye className="w-3.5 h-3.5" />
                  Audit & Decide
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Review Modal */}
      <Modal
        isOpen={!!reviewReport}
        onClose={() => { setReviewReport(null); setComments(''); }}
        title={`Audit Handover Dossier: ${reviewReport?.title || ''}`}
        maxWidth="xl"
      >
        {reviewReport && (
          <div className="space-y-4 text-xs">
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <div className="grid grid-cols-2 gap-2 text-slate-600">
                <div><span className="font-semibold text-slate-900">Project:</span> {reviewReport.project_name}</div>
                <div><span className="font-semibold text-slate-900">Version:</span> v{reviewReport.version}</div>
                <div><span className="font-semibold text-slate-900">Author:</span> {reviewReport.creator_name}</div>
                <div><span className="font-semibold text-slate-900">Current Status:</span> {reviewReport.status}</div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Reviewer Governance Comments & Sign-off Notes
              </label>
              <textarea
                rows={3}
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                placeholder="Specify verification remarks, checklist validation, or required revisions..."
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
              />
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => handleDownloadPdf(reviewReport.id)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:text-slate-900 flex items-center gap-1"
              >
                <Download className="w-3.5 h-3.5" /> Inspect PDF Export
              </button>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={submitting}
                  onClick={() => handleReject(reviewReport.id)}
                  className="px-3.5 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
                >
                  Reject with Notes
                </button>
                <button
                  type="button"
                  disabled={submitting}
                  onClick={() => handleApprove(reviewReport.id)}
                  className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition-colors flex items-center gap-1 disabled:opacity-50"
                >
                  <Check className="w-3.5 h-3.5" />
                  {submitting ? 'Recording...' : 'Officially Approve'}
                </button>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

