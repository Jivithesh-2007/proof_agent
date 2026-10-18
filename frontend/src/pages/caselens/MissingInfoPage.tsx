import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  FileQuestion,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  RefreshCw,
  ShieldCheck,
  FileText,
  Info,
} from 'lucide-react';
import { caselensApi } from '../../services/caselensApi';
import { MissingInfoAnalysisResponse } from '../../types/caselens';

export const MissingInfoPage: React.FC = () => {
  const { currentWs } = useOutletContext<{ currentWs: string }>();

  const [template, setTemplate] = useState<string>('service_agreement');
  const [data, setData] = useState<MissingInfoAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadMissingInfo(template);
  }, [currentWs, template]);

  const loadMissingInfo = async (tpl: string) => {
    setLoading(true);
    try {
      const resp = await caselensApi.getMissingInfo(currentWs, tpl);
      setData(resp);
    } catch (e) {
      console.error('Failed to load missing info analysis', e);
    } finally {
      setLoading(false);
    }
  };

  const templates = [
    { id: 'service_agreement', name: 'Master Services Agreement (MSA)' },
    { id: 'employment_agreement', name: 'Executive Employment Agreement' },
    { id: 'commercial_lease', name: 'Commercial Warehouse Lease' },
    { id: 'general_contract', name: 'General Contract Review' },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
              Contract Completeness Checklist
            </span>
            <span className="text-xs text-[var(--text-muted)]">Benchmark Template Audit</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
            Missing-Information Analysis
          </h1>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Evaluates uploaded legal documents against standard contract templates to detect absent protective clauses.
          </p>
        </div>

        <button
          onClick={() => loadMissingInfo(template)}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs flex items-center gap-2 transition-all disabled:opacity-50 self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Evaluating...' : 'Re-Run Audit'}</span>
        </button>
      </div>

      {/* Template Selector Bar */}
      <div className="p-4 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-[var(--text-muted)]">Template Benchmark:</span>
          <div className="flex flex-wrap items-center gap-1.5">
            {templates.map((t) => (
              <button
                key={t.id}
                onClick={() => setTemplate(t.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  template === t.id
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'bg-[var(--bg-input)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-input)]/80'
                }`}
              >
                {t.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Summary Scorecard */}
      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-1">
            <span className="text-xs text-[var(--text-muted)]">Present Standard Clauses</span>
            <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
              {data.present_count}
            </p>
            <p className="text-[11px] text-[var(--text-muted)]">Verified in current document corpus</p>
          </div>

          <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-1">
            <span className="text-xs text-[var(--text-muted)]">Missing Expected Clauses</span>
            <p className="text-2xl font-bold text-red-600 dark:text-red-400">
              {data.missing_count}
            </p>
            <p className="text-[11px] text-[var(--text-muted)]">Not identified in document corpus</p>
          </div>

          <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-1">
            <span className="text-xs text-[var(--text-muted)]">Ambiguous / Abbreviated</span>
            <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">
              {data.ambiguous_count}
            </p>
            <p className="text-[11px] text-[var(--text-muted)]">Requires manual confirmation</p>
          </div>
        </div>
      )}

      {/* Disclaimer Alert */}
      <div className="p-3.5 rounded-xl bg-blue-50/70 dark:bg-blue-950/20 border border-blue-200/60 dark:border-blue-900/60 text-xs flex items-center gap-2 text-blue-900 dark:text-blue-300">
        <Info className="w-4 h-4 shrink-0 text-blue-600" />
        <span>
          <strong>Methodological Note:</strong> {data?.disclaimer ||
            'Missing information reflects a template comparison observation and does not constitute formal legal invalidity.'}
        </span>
      </div>

      {/* Checklist Table */}
      <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[var(--bg-input)]/50 border-b border-[var(--border-color)] text-[var(--text-muted)] uppercase tracking-wider font-semibold">
              <tr>
                <th className="py-3 px-4">Expected Clause</th>
                <th className="py-3 px-3">Category</th>
                <th className="py-3 px-3">Importance</th>
                <th className="py-3 px-3">Audit Status</th>
                <th className="py-3 px-4">Review Observation & Evidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-color)]">
              {data?.checks.map((chk, idx) => (
                <tr key={idx} className="hover:bg-[var(--bg-input)]/30 transition-colors">
                  <td className="py-3 px-4 font-bold text-[var(--text-primary)]">
                    {chk.field_name}
                  </td>
                  <td className="py-3 px-3 text-[var(--text-muted)]">
                    {chk.category}
                  </td>
                  <td className="py-3 px-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      chk.expected_importance === 'critical'
                        ? 'bg-red-500/10 text-red-600'
                        : chk.expected_importance === 'standard'
                        ? 'bg-blue-500/10 text-blue-600'
                        : 'bg-gray-500/10 text-gray-600'
                    }`}>
                      {chk.expected_importance}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold inline-flex items-center gap-1 ${
                      chk.status === 'present'
                        ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                        : chk.status === 'ambiguous'
                        ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
                        : 'bg-red-500/15 text-red-600 dark:text-red-400'
                    }`}>
                      {chk.status === 'present' ? (
                        <CheckCircle2 className="w-3 h-3" />
                      ) : chk.status === 'ambiguous' ? (
                        <HelpCircle className="w-3 h-3" />
                      ) : (
                        <AlertCircle className="w-3 h-3" />
                      )}
                      {chk.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-[var(--text-muted)] max-w-md">
                    <p className="text-[var(--text-primary)] font-medium">{chk.review_note}</p>
                    {chk.found_evidence && (
                      <p className="mt-1 font-mono text-[10px] text-[var(--text-muted)] italic truncate">
                        Found snippet: “{chk.found_evidence}”
                      </p>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
