import React, { useState, useEffect, useRef } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  FileText,
  UploadCloud,
  Trash2,
  Eye,
  Search,
  CheckCircle2,
  AlertCircle,
  FileCode,
  RotateCcw,
  Clock,
  HardDrive,
  Hash,
  X,
  Filter,
} from 'lucide-react';
import { caselensApi } from '../../services/caselensApi';
import { DocumentMetadata, DocumentChunk } from '../../types/caselens';

export const DocumentsPage: React.FC = () => {
  const { currentWs } = useOutletContext<{ currentWs: string }>();

  const [docs, setDocs] = useState<DocumentMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<DocumentMetadata | null>(null);
  const [previewChunks, setPreviewChunks] = useState<DocumentChunk[]>([]);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewSearch, setPreviewSearch] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadDocs();
  }, [currentWs]);

  const loadDocs = async () => {
    setLoading(true);
    try {
      const data = await caselensApi.listDocuments(currentWs);
      setDocs(data);
    } catch (e) {
      console.error('Failed to load documents', e);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    setUploadError(null);

    try {
      for (let i = 0; i < files.length; i++) {
        await caselensApi.uploadDocument(currentWs, files[i]);
      }
      await loadDocs();
    } catch (err: any) {
      setUploadError(err.message || 'Upload failed.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (docId: string) => {
    try {
      await caselensApi.deleteDocument(docId);
      setDocs(docs.filter(d => d.document_id !== docId));
      if (selectedDoc?.document_id === docId) {
        setSelectedDoc(null);
        setPreviewChunks([]);
      }
    } catch (e) {
      alert('Failed to delete document: ' + e);
    } finally {
      setDeleteConfirmId(null);
    }
  };

  const openPreview = async (doc: DocumentMetadata) => {
    setSelectedDoc(doc);
    setPreviewLoading(true);
    try {
      const chunks = await caselensApi.getDocumentChunks(doc.document_id);
      setPreviewChunks(chunks);
    } catch (e) {
      console.error('Failed to load document chunks', e);
    } finally {
      setPreviewLoading(false);
    }
  };

  const filteredDocs = docs.filter(d =>
    d.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
    d.file_type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredChunks = previewChunks.filter(c =>
    previewSearch ? c.text.toLowerCase().includes(previewSearch.toLowerCase()) : true
  );

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
            Document Repository
          </h1>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Upload PDF, DOCX, and TXT files. Cryptographic hashes and page boundaries are extracted and persisted in SQLite.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => handleFileUpload(e.target.files)}
            className="hidden"
            multiple
            accept=".pdf,.docx,.txt"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs flex items-center gap-2 transition-all disabled:opacity-50"
          >
            <UploadCloud className="w-4 h-4" />
            <span>{uploading ? 'Processing File...' : 'Upload Document'}</span>
          </button>
        </div>
      </div>

      {uploadError && (
        <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{uploadError}</span>
          </div>
          <button onClick={() => setUploadError(null)} className="text-xs hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Drag & Drop Upload Dropzone */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          handleFileUpload(e.dataTransfer.files);
        }}
        onClick={() => fileInputRef.current?.click()}
        className="p-8 border-2 border-dashed border-[var(--border-color)] hover:border-blue-500 rounded-2xl bg-[var(--bg-card)] text-center cursor-pointer transition-all space-y-2 group"
      >
        <div className="w-12 h-12 rounded-full bg-blue-50 dark:bg-blue-950/40 text-blue-600 flex items-center justify-center mx-auto group-hover:scale-110 transition-transform">
          <UploadCloud className="w-6 h-6" />
        </div>
        <p className="text-sm font-semibold text-[var(--text-primary)]">
          Click or drag & drop documents here
        </p>
        <p className="text-xs text-[var(--text-muted)]">
          Supports PDF (PyMuPDF with page offsets), DOCX, and TXT files up to 50MB.
        </p>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)]">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-[var(--text-muted)]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search documents by name or format..."
            className="w-full text-xs bg-[var(--bg-input)] border border-[var(--border-color)] rounded-lg pl-9 pr-3 py-2 text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <div className="text-xs text-[var(--text-muted)] font-medium">
          Showing {filteredDocs.length} of {docs.length} document(s)
        </div>
      </div>

      {/* Document Library Table */}
      <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[var(--bg-input)]/50 border-b border-[var(--border-color)] text-[var(--text-muted)] uppercase tracking-wider font-semibold">
              <tr>
                <th className="py-3 px-4">Document</th>
                <th className="py-3 px-3">Type</th>
                <th className="py-3 px-3">Size</th>
                <th className="py-3 px-3">Pages / Chunks</th>
                <th className="py-3 px-3">SHA-256 Provenance</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-color)]">
              {filteredDocs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-[var(--text-muted)]">
                    No documents found matching query.
                  </td>
                </tr>
              ) : (
                filteredDocs.map((doc) => (
                  <tr key={doc.document_id} className="hover:bg-[var(--bg-input)]/30 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2.5">
                        <FileText className="w-4 h-4 text-blue-600 shrink-0" />
                        <div>
                          <p className="font-semibold text-[var(--text-primary)]">{doc.filename}</p>
                          <p className="text-[10px] text-[var(--text-muted)] font-mono">{doc.document_id}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="uppercase font-semibold text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-input)] text-[var(--text-muted)]">
                        {doc.file_type}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-[var(--text-muted)] font-mono">
                      {(doc.file_size_bytes / 1024).toFixed(1)} KB
                    </td>
                    <td className="py-3 px-3 text-[var(--text-muted)]">
                      {doc.page_count} page(s) · {doc.chunk_count} chunk(s)
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-mono text-[10px] text-[var(--text-muted)]" title={doc.content_hash}>
                        {doc.content_hash.substring(0, 12)}...
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold inline-flex items-center gap-1 ${
                        doc.processing_status === 'processed'
                          ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                          : 'bg-red-500/10 text-red-600 dark:text-red-400'
                      }`}>
                        <CheckCircle2 className="w-3 h-3" />
                        {doc.processing_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => openPreview(doc)}
                          className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-blue-600 hover:bg-[var(--bg-input)] transition-colors"
                          title="Preview Extracted Text"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        {deleteConfirmId === doc.document_id ? (
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => handleDelete(doc.document_id)}
                              className="px-2 py-1 bg-red-600 text-white rounded text-[10px] font-bold"
                            >
                              Confirm
                            </button>
                            <button
                              onClick={() => setDeleteConfirmId(null)}
                              className="px-2 py-1 bg-[var(--bg-input)] text-[var(--text-muted)] rounded text-[10px]"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setDeleteConfirmId(doc.document_id)}
                            className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-red-600 hover:bg-[var(--bg-input)] transition-colors"
                            title="Delete Document"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Document Preview Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="w-full max-w-4xl h-[85vh] rounded-2xl bg-[var(--bg-card)] border border-[var(--border-color)] shadow-2xl flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 border-b border-[var(--border-color)] flex items-center justify-between bg-[var(--bg-input)]/40">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                <div>
                  <h3 className="font-bold text-sm text-[var(--text-primary)]">
                    {selectedDoc.filename}
                  </h3>
                  <p className="text-[11px] text-[var(--text-muted)]">
                    {selectedDoc.page_count} Page(s) · {previewChunks.length} Chunks · SHA-256: {selectedDoc.content_hash.substring(0, 16)}...
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedDoc(null)}
                className="p-1.5 rounded-lg text-[var(--text-muted)] hover:bg-[var(--bg-input)] hover:text-[var(--text-primary)] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Search Bar */}
            <div className="p-3 border-b border-[var(--border-color)] bg-[var(--bg-card)]">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-[var(--text-muted)]" />
                <input
                  type="text"
                  value={previewSearch}
                  onChange={(e) => setPreviewSearch(e.target.value)}
                  placeholder="Filter extracted passages in this document..."
                  className="w-full text-xs bg-[var(--bg-input)] border border-[var(--border-color)] rounded-lg pl-9 pr-3 py-1.5 text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {previewLoading ? (
                <div className="p-12 text-center text-xs text-[var(--text-muted)]">
                  Loading extracted document passages...
                </div>
              ) : filteredChunks.length === 0 ? (
                <div className="p-12 text-center text-xs text-[var(--text-muted)]">
                  No passages found matching search filter.
                </div>
              ) : (
                filteredChunks.map((chunk, idx) => (
                  <div
                    key={chunk.chunk_id || idx}
                    className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-input)]/20 space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between text-[11px] font-semibold text-[var(--text-muted)] pb-1 border-b border-[var(--border-color)]">
                      <span className="text-blue-600 dark:text-blue-400">Page {chunk.page_number}</span>
                      <span className="font-mono text-[10px]">
                        Offset [{chunk.char_start} : {chunk.char_end}]
                      </span>
                    </div>
                    <p className="text-[var(--text-primary)] leading-relaxed font-mono whitespace-pre-wrap">
                      {chunk.text}
                    </p>
                  </div>
                ))
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-3 border-t border-[var(--border-color)] bg-[var(--bg-input)]/30 flex items-center justify-between text-xs text-[var(--text-muted)]">
              <span>Extracted using PyMuPDF / python-docx preserving verbatim page boundaries.</span>
              <button
                onClick={() => setSelectedDoc(null)}
                className="px-4 py-1.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] font-semibold text-[var(--text-primary)] hover:bg-[var(--bg-input)] transition-colors"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
