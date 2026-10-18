import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  GitCompare,
  FileText,
  ArrowRight,
  RefreshCw,
  PlusCircle,
  MinusCircle,
  Edit3,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { caselensApi } from '../../services/caselensApi';
import { DocumentMetadata, DocumentComparisonResponse } from '../../types/caselens';

export const DocumentComparisonPage: React.FC = () => {
  const { currentWs } = useOutletContext<{ currentWs: string }>();

  const [docs, setDocs] = useState<DocumentMetadata[]>([]);
  const [docAId, setDocAId] = useState<string>('');
  const [docBId, setDocBId] = useState<string>('');
  const [comparison, setComparison] = useState<DocumentComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');

  useEffect(() => {
    loadDocs();
  }, [currentWs]);

  const loadDocs = async () => {
    try {
      const list = await caselensApi.listDocuments(currentWs);
      setDocs(list);
      if (list.length >= 2) {
        setDocAId(list[0].document_id);
        setDocBId(list[1].document_id);
        runComparison(list[0].document_id, list[1].document_id);
      }
    } catch (e) {
      console.error('Failed to load documents for comparison', e);
    }
  };

  const runComparison = async (aId?: string, bId?: string) => {
    const idA = aId || docAId;
    const idB = bId || docBId;
    if (!idA || !idB || idA === idB) return;

    setLoading(true);
    try {
      const resp = await caselensApi.compareDocuments(idA, idB);
      setComparison(resp);
    } catch (e: any) {
      alert('Comparison failed: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const clauses = comparison?.clause_comparisons || [];
  const filteredClauses = filterType === 'all'
    ? clauses
    : clauses.filter(c => c.change_type === filterType);

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/15 text-indigo-600 dark:text-indigo-400">
            Document Diff & Revision Intelligence
          </span>
          <span className="text-xs text-[var(--text-muted)]">Side-by-Side Clause Alignment</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
          Document Comparison
        </h1>
        <p className="text-xs text-[var(--text-muted)] mt-1">
          Select two agreements or addenda to evaluate changed monetary terms, modified covenants, and added/removed clauses.
        </p>
      </div>

      {/* Selector Card */}
      <div className="p-5 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-xs space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-center">
          {/* Doc A */}
          <div className="md:col-span-2 space-y-1.5">
            <label className="text-xs font-bold text-[var(--text-muted)] flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-blue-600" />
              <span>Base Document (A)</span>
            </label>
            <select
              value={docAId}
              onChange={(e) => setDocAId(e.target.value)}
              className="w-full text-xs font-medium bg-[var(--bg-input)] border border-[var(--border-color)] rounded-xl px-3 py-2 text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
            >
              {docs.map((d) => (
                <option key={d.document_id} value={d.document_id} disabled={d.document_id === docBId}>
                  {d.filename}
                </option>
              ))}
            </select>
          </div>

          {/* Compare Icon / CTA */}
          <div className="md:col-span-1 flex justify-center">
            <button
              onClick={() => runComparison()}
              disabled={loading || docAId === docBId || !docAId || !docBId}
              className="p-3 rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-all disabled:opacity-40"
              title="Execute Comparison"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {/* Doc B */}
          <div className="md:col-span-2 space-y-1.5">
            <label className="text-xs font-bold text-[var(--text-muted)] flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-indigo-600" />
              <span>Comparison Document (B)</span>
            </label>
            <select
              value={docBId}
              onChange={(e) => setDocBId(e.target.value)}
              className="w-full text-xs font-medium bg-[var(--bg-input)] border border-[var(--border-color)] rounded-xl px-3 py-2 text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
            >
              {docs.map((d) => (
                <option key={d.document_id} value={d.document_id} disabled={d.document_id === docAId}>
                  {d.filename}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Metrics Summary Strip */}
        {comparison && (
          <div className="pt-4 border-t border-[var(--border-color)] grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div className="p-3 rounded-xl bg-[var(--bg-input)]/40 space-y-1">
              <span className="text-[var(--text-muted)]">Structural Similarity</span>
              <p className="text-lg font-bold text-blue-600 dark:text-blue-400">
                {comparison.similarity_score}%
              </p>
            </div>
            <div className="p-3 rounded-xl bg-[var(--bg-input)]/40 space-y-1">
              <span className="text-[var(--text-muted)]">Modified Clauses</span>
              <p className="text-lg font-bold text-amber-600 dark:text-amber-400">
                {comparison.modified_clauses}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-[var(--bg-input)]/40 space-y-1">
              <span className="text-[var(--text-muted)]">Added Clauses</span>
              <p className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
                {comparison.added_clauses}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-[var(--bg-input)]/40 space-y-1">
              <span className="text-[var(--text-muted)]">Removed Clauses</span>
              <p className="text-lg font-bold text-red-600 dark:text-red-400">
                {comparison.removed_clauses}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Key Differences Highlight Card */}
      {comparison && comparison.key_differences.length > 0 && (
        <div className="p-5 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-xs space-y-3">
          <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-500" />
            <span>Key Substantive Differences Identified</span>
          </h3>
          <ul className="space-y-1.5 text-xs text-[var(--text-muted)]">
            {comparison.key_differences.map((diff, i) => (
              <li key={i} className="flex items-start gap-2 p-2 rounded-lg bg-[var(--bg-input)]/30 font-medium text-[var(--text-primary)]">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 shrink-0" />
                <span>{diff}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 text-xs font-semibold overflow-x-auto pb-1">
        <button
          onClick={() => setFilterType('all')}
          className={`px-3 py-1.5 rounded-lg transition-colors ${
            filterType === 'all'
              ? 'bg-blue-600 text-white'
              : 'bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-muted)]'
          }`}
        >
          All Clauses ({clauses.length})
        </button>
        <button
          onClick={() => setFilterType('modified')}
          className={`px-3 py-1.5 rounded-lg transition-colors ${
            filterType === 'modified'
              ? 'bg-blue-600 text-white'
              : 'bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-muted)]'
          }`}
        >
          Modified ({comparison?.modified_clauses || 0})
        </button>
        <button
          onClick={() => setFilterType('added_in_b')}
          className={`px-3 py-1.5 rounded-lg transition-colors ${
            filterType === 'added_in_b'
              ? 'bg-blue-600 text-white'
              : 'bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-muted)]'
          }`}
        >
          Added in B ({comparison?.added_clauses || 0})
        </button>
        <button
          onClick={() => setFilterType('removed_in_b')}
          className={`px-3 py-1.5 rounded-lg transition-colors ${
            filterType === 'removed_in_b'
              ? 'bg-blue-600 text-white'
              : 'bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-muted)]'
          }`}
        >
          Removed in B ({comparison?.removed_clauses || 0})
        </button>
      </div>

      {/* Side-by-Side Clause Comparisons */}
      <div className="space-y-4">
        {filteredClauses.map((clause, idx) => (
          <div
            key={idx}
            className="p-5 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-xs space-y-3 text-xs"
          >
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border-color)]">
              <span className="font-bold text-sm text-[var(--text-primary)]">
                {clause.section_title}
              </span>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                clause.change_type === 'identical'
                  ? 'bg-emerald-500/10 text-emerald-600'
                  : clause.change_type === 'modified'
                  ? 'bg-amber-500/15 text-amber-600'
                  : clause.change_type === 'added_in_b'
                  ? 'bg-blue-500/15 text-blue-600'
                  : 'bg-red-500/15 text-red-600'
              }`}>
                {clause.change_type.replace('_', ' ')}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Doc A Text */}
              <div className="p-3 rounded-xl bg-[var(--bg-input)]/25 border border-[var(--border-color)] space-y-1">
                <span className="text-[10px] font-semibold text-[var(--text-muted)]">
                  {comparison?.doc_a_name} (Document A)
                </span>
                <p className="font-mono leading-relaxed text-[var(--text-primary)]">
                  {clause.doc_a_text || <span className="text-[var(--text-muted)] italic">[Not present in Document A]</span>}
                </p>
              </div>

              {/* Doc B Text */}
              <div className="p-3 rounded-xl bg-[var(--bg-input)]/25 border border-[var(--border-color)] space-y-1">
                <span className="text-[10px] font-semibold text-[var(--text-muted)]">
                  {comparison?.doc_b_name} (Document B)
                </span>
                <p className="font-mono leading-relaxed text-[var(--text-primary)]">
                  {clause.doc_b_text || <span className="text-[var(--text-muted)] italic">[Omitted in Document B]</span>}
                </p>
              </div>
            </div>

            <div className="text-[11px] text-[var(--text-muted)] pt-1 flex items-center gap-1.5">
              <span className="font-semibold text-[var(--text-primary)]">Observation:</span>
              <span>{clause.observation}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
