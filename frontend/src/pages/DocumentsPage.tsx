import React, { useEffect, useState, useRef } from 'react';
import {
  FileText,
  Upload,
  Trash2,
  Eye,
  CheckCircle2,
  AlertCircle,
  Clock,
  FolderGit2
} from 'lucide-react';
import { projectApi, documentApi } from '../services/api';
import { Project, ProjectDocument, DocumentChunk } from '../types';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { EmptyState } from '../components/common/EmptyState';

export const DocumentsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [documents, setDocuments] = useState<ProjectDocument[]>([]);
  const [loading, setLoading] = useState(true);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Inspector modal
  const [inspectDoc, setInspectDoc] = useState<ProjectDocument | null>(null);
  const [docChunks, setDocChunks] = useState<DocumentChunk[]>([]);
  const [loadingChunks, setLoadingChunks] = useState(false);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      loadDocuments(selectedProjectId);
    }
  }, [selectedProjectId]);

  const fetchInitialData = async () => {
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

  const loadDocuments = async (projId: number) => {
    try {
      const docs = await documentApi.list(projId);
      setDocuments(docs);
    } catch (err) {
      console.error(err);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!selectedProjectId) return;
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setUploadError(null);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      await documentApi.upload(selectedProjectId, formData);
      await loadDocuments(selectedProjectId);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Failed to upload files.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId: number) => {
    if (!selectedProjectId) return;
    if (!window.confirm('Delete this document and remove its chunks from vector search?')) return;
    try {
      await documentApi.delete(docId);
      setDocuments(documents.filter((d) => d.id !== docId));
    } catch (err) {
      console.error(err);
    }
  };

  const handleInspectChunks = async (doc: ProjectDocument) => {
    setInspectDoc(doc);
    setLoadingChunks(true);
    try {
      const chunks = await documentApi.getChunks(doc.id);
      setDocChunks(chunks);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingChunks(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Project Select */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Document Ingestion Pipeline</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Extracts, chunks, embeds, and indexes project source documents into ChromaDB.
          </p>
        </div>

        {projects.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-slate-600">Active Workspace:</span>
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

      {projects.length === 0 ? (
        <EmptyState
          icon={FolderGit2}
          title="No projects available"
          description="Create a project first before uploading source documentation."
          actionText="Create Project"
          onAction={() => window.location.href = '/projects'}
        />
      ) : (
        <>
          {/* Drag & Drop Upload Container */}
          <div className="bg-white p-6 rounded-xl border-2 border-dashed border-slate-200 hover:border-teal-500 transition-colors text-center shadow-xs">
            <input
              type="file"
              ref={fileInputRef}
              multiple
              accept=".pdf,.docx,.doc,.txt,.csv,.md"
              onChange={handleFileUpload}
              className="hidden"
              id="main-doc-upload"
            />
            <label htmlFor="main-doc-upload" className="cursor-pointer flex flex-col items-center">
              <div className="w-12 h-12 rounded-full bg-teal-50 flex items-center justify-center text-teal-600 mb-2 border border-teal-100">
                <Upload className="w-6 h-6" />
              </div>
              <span className="text-xs font-semibold text-slate-800">
                Drag and drop project files or browse to upload
              </span>
              <span className="text-[11px] text-slate-500 mt-1">
                PyMuPDF (PDF), python-docx (DOCX), pandas (CSV), and TXT
              </span>
            </label>
            {uploading && (
              <div className="mt-3 text-xs text-teal-600 font-mono animate-pulse">
                Parsing text, dividing into semantic chunks, and storing dense vectors...
              </div>
            )}
            {uploadError && (
              <div className="mt-3 text-xs text-rose-600 font-medium">{uploadError}</div>
            )}
          </div>

          {/* Ingested Document Table */}
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Ingested Documents ({documents.length})
              </h3>
              <span className="text-[11px] text-slate-500 font-mono">ChromaDB Semantic Store</span>
            </div>

            {documents.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-400">
                No documents uploaded for this project yet.
              </div>
            ) : (
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-medium border-b border-slate-100">
                  <tr>
                    <th className="px-5 py-2.5">File Name</th>
                    <th className="px-4 py-2.5">Format</th>
                    <th className="px-4 py-2.5">Extracted Chunks</th>
                    <th className="px-4 py-2.5">Size</th>
                    <th className="px-4 py-2.5">Processing Status</th>
                    <th className="px-4 py-2.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-slate-50/50">
                      <td className="px-5 py-3 font-semibold text-slate-900 flex items-center gap-2">
                        <FileText className="w-4 h-4 text-slate-400" />
                        <span>{doc.filename}</span>
                      </td>
                      <td className="px-4 py-3 uppercase text-slate-500 font-mono text-[11px]">
                        {doc.file_type}
                      </td>
                      <td className="px-4 py-3 text-slate-700">{doc.chunk_count} chunks</td>
                      <td className="px-4 py-3 text-slate-500">
                        {(doc.file_size / 1024).toFixed(1)} KB
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={
                            doc.processing_status === 'processed'
                              ? 'verified'
                              : doc.processing_status === 'failed'
                              ? 'conflicting'
                              : 'needs_review'
                          }
                        >
                          {doc.processing_status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleInspectChunks(doc)}
                            className="p-1 text-slate-500 hover:text-teal-600 rounded hover:bg-slate-100"
                            title="Inspect Text Chunks"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(doc.id)}
                            className="p-1 text-slate-500 hover:text-rose-600 rounded hover:bg-slate-100"
                            title="Delete Document"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}

      {/* Chunks Inspector Modal */}
      <Modal
        isOpen={!!inspectDoc}
        onClose={() => setInspectDoc(null)}
        title={`Extracted Chunks: ${inspectDoc?.filename || ''}`}
        maxWidth="2xl"
      >
        {loadingChunks ? (
          <div className="text-center py-8 text-xs text-slate-500 font-mono animate-pulse">
            Fetching chunks...
          </div>
        ) : (
          <div className="space-y-3">
            {docChunks.map((c) => (
              <div key={c.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1.5 font-mono">
                  <span>Chunk Index #{c.chunk_index}</span>
                  <span>Page {c.page_number || 1}</span>
                </div>
                <p className="text-slate-800 leading-relaxed font-mono text-[11px]">
                  {c.extracted_text}
                </p>
              </div>
            ))}
          </div>
        )}
      </Modal>
    </div>
  );
};

