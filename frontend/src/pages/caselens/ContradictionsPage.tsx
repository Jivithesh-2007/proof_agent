import React, { useState, useEffect } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  FileText,
  RefreshCw,
  Scale,
  Calendar,
  DollarSign,
  Clock,
  ArrowRight,
  ShieldAlert,
  CheckCircle2,
} from 'lucide-react';
import { caselensApi } from '../../services/caselensApi';
import { ContradictionResponse, ContradictionItem } from '../../types/caselens';

export const ContradictionsPage: React.FC = () => {
  const { currentWs } = useOutletContext<{ currentWs: string }>();
  const navigate = useNavigate();

  const [data, setData] = useState<ContradictionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedFilter, setSelectedFilter] = useState<string>('all');

  useEffect(() => {
    loadContradictions();
  }, [currentWs]);

  const loadContradictions = async () => {
    setLoading(true);
    try {
      const resp = await caselensApi.getContradictions(currentWs);
      setData(resp);
    } catch (e) {
      console.error('Failed to load contradictions', e);
    } finally {
      setLoading(false);
    }
  };

  const findings = data?.findings || [];
  const filteredFindings = selectedFilter === 'all'
    ? findings
    : findings.filter(f => f.category.toLowerCase().includes(selectedFilter.toLowerCase()));

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-500/15 text-amber-600 dark:text-amber-400">
              Cross-Document Conflict Engine
            </span>
            <span className="text-xs text-[var(--text-muted)]">Mode: Deterministic Rule Verifier</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
            Contradiction & Discrepancy Analysis
          </h1>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Surfaces conflicting termination dates, payment amounts, and notice periods across documents in this workspace.
          </p>
        </div>

        <button
          onClick={loadContradictions}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs flex items-center gap-2 transition-all disabled:opacity-50 self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Scanning Documents...' : 'Re-Scan Contradictions'}</span>
        </button>
      </div>

      {/* Summary Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-1">
          <span className="text-xs text-[var(--text-muted)]">Potential Contradictions</span>
          <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">
            {findings.length}
          </p>
          <p className="text-[11px] text-[var(--text-muted)]">Evaluated across all active files</p>
        </div>

        <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-1">
          <span className="text-xs text-[var(--text-muted)]">High Severity Conflicts</span>
          <p className="text-2xl font-bold text-red-600 dark:text-red-400">
            {findings.filter(f => f.severity === 'high').length}
          </p>
          <p className="text-[11px] text-[var(--text-muted)]">Requires legal addendum alignment</p>
        </div>

        <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-1">
          <span className="text-xs text-[var(--text-muted)]">Evaluation Engine</span>
          <p className="text-xs font-bold text-[var(--text-primary)] mt-1">
            Exact Invariant Matching
          </p>
          <p className="text-[11px] text-[var(--text-muted)]">Zero false positive context conflation</p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 text-xs font-semibold overflow-x-auto pb-1">
        <button
          onClick={() => setSelectedFilter('all')}
          className={`px-3 py-1.5 rounded-lg transition-colors ${
            selectedFilter === 'all'
              ? 'bg-blue-600 text-white'
              : 'bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-muted)] hover:text-[var(--text-primary)]'
          }`}
        >
          All ({findings.length})
        </button>
        <button
          onClick={() => setSelectedFilter('date')}
          className={`px-3 py-1.5 rounded-lg transition-colors ${
            selectedFilter === 'date'
              ? 'bg-blue-600 text-white'
              : 'bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-muted)] hover:text-[var(--text-primary)]'
          }`}
        >
          Date Mismatches
        </button>
        <button
          onClick={() => setSelectedFilter('payment')}
          className={`px-3 py-1.5 rounded-lg transition-colors ${
            selectedFilter === 'payment'
              ? 'bg-blue-600 text-white'
              : 'bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-muted)] hover:text-[var(--text-primary)]'
          }`}
        >
          Payment Conflicts
        </button>
        <button
          onClick={() => setSelectedFilter('notice')}
          className={`px-3 py-1.5 rounded-lg transition-colors ${
            selectedFilter === 'notice'
              ? 'bg-blue-600 text-white'
              : 'bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-muted)] hover:text-[var(--text-primary)]'
          }`}
        >
          Notice Period Discrepancies
        </button>
      </div>

      {/* Contradiction Cards */}
      <div className="space-y-4">
        {filteredFindings.length === 0 ? (
          <div className="p-12 text-center rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] text-xs text-[var(--text-muted)] space-y-2">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
            <p className="font-semibold text-sm text-[var(--text-primary)]">
              No contradictions detected in this category.
            </p>
            <p>Documents show mutually consistent contractual stipulations for selected criteria.</p>
          </div>
        ) : (
          filteredFindings.map((finding) => (
            <div
              key={finding.contradiction_id}
              className="p-6 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-xs space-y-4"
            >
              {/* Card Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[var(--border-color)]">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-amber-500/15 text-amber-600 flex items-center justify-center shrink-0">
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-[var(--text-primary)]">
                      {finding.summary}
                    </h3>
                    <p className="text-[11px] text-[var(--text-muted)]">
                      Category: <strong>{finding.category}</strong> · Ref: <span className="font-mono">{finding.contradiction_id}</span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                    finding.severity === 'high'
                      ? 'bg-red-500/15 text-red-600 dark:text-red-400'
                      : 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
                  }`}>
                    {finding.severity} Severity
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full bg-[var(--bg-input)] text-[var(--text-muted)] text-[10px] font-semibold">
                    {finding.status}
                  </span>
                </div>
              </div>

              {/* Side-by-Side Source Passages */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                {/* Passage A */}
                <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-input)]/25 space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-semibold text-[var(--text-primary)]">
                    <span className="flex items-center gap-1.5 truncate">
                      <FileText className="w-3.5 h-3.5 text-blue-600" />
                      {finding.doc_a_name}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-muted)]">
                      Page {finding.doc_a_page}
                    </span>
                  </div>
                  <p className="p-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] font-mono text-[11px] text-[var(--text-primary)] leading-relaxed italic">
                    “{finding.doc_a_passage}”
                  </p>
                </div>

                {/* Passage B */}
                <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-input)]/25 space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-semibold text-[var(--text-primary)]">
                    <span className="flex items-center gap-1.5 truncate">
                      <FileText className="w-3.5 h-3.5 text-blue-600" />
                      {finding.doc_b_name}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-muted)]">
                      Page {finding.doc_b_page}
                    </span>
                  </div>
                  <p className="p-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] font-mono text-[11px] text-[var(--text-primary)] leading-relaxed italic">
                    “{finding.doc_b_passage}”
                  </p>
                </div>
              </div>

              {/* Recommendation Banner */}
              <div className="p-3.5 rounded-xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-300/60 dark:border-amber-800/60 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <span className="font-bold text-amber-900 dark:text-amber-200">Legal Review Observation:</span>
                  <p className="text-amber-800 dark:text-amber-300/90 mt-0.5">
                    {finding.review_recommendation}
                  </p>
                </div>
                <button
                  onClick={() => navigate('/caselens/reports')}
                  className="px-3 py-1.5 rounded-lg bg-[var(--bg-card)] border border-amber-300 dark:border-amber-800 text-[11px] font-semibold text-[var(--text-primary)] hover:bg-[var(--bg-input)] shrink-0 transition-colors"
                >
                  Include in Report →
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
