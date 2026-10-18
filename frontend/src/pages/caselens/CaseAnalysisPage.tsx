import React, { useState, useEffect } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import {
  Scale,
  Calendar,
  Users,
  AlertTriangle,
  FileCheck,
  RefreshCw,
  Shield,
  Clock,
  Layers,
  ArrowRight,
  ExternalLink,
  CheckCircle2,
} from 'lucide-react';
import { caselensApi } from '../../services/caselensApi';
import { CaseAnalysisResponse } from '../../types/caselens';

export const CaseAnalysisPage: React.FC = () => {
  const { currentWs } = useOutletContext<{ currentWs: string }>();
  const navigate = useNavigate();

  const [analysis, setAnalysis] = useState<CaseAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'obligations' | 'timeline' | 'entities' | 'risks' | 'evidence'>('obligations');

  useEffect(() => {
    loadAnalysis();
  }, [currentWs]);

  const loadAnalysis = async () => {
    setLoading(true);
    try {
      const data = await caselensApi.getCaseAnalysis(currentWs);
      setAnalysis(data);
    } catch (e) {
      console.error('Failed to load case analysis', e);
    } finally {
      setLoading(false);
    }
  };

  const handleReanalyze = async () => {
    setLoading(true);
    try {
      const data = await caselensApi.triggerCaseAnalysis(currentWs);
      setAnalysis(data);
    } catch (e) {
      alert('Analysis execution failed: ' + e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-600/10 text-blue-600 dark:text-blue-400">
              Structured Case Analysis
            </span>
            <span className="text-xs text-[var(--text-muted)] font-mono">{analysis?.analysis_id}</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
            {analysis?.case_title || 'Legal Document Portfolio Analysis'}
          </h1>
        </div>

        <button
          onClick={handleReanalyze}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs flex items-center gap-2 transition-all disabled:opacity-50 self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Analyzing Corpus...' : 'Re-Run Case Analysis'}</span>
        </button>
      </div>

      {/* Executive Summary Card */}
      <div className="p-6 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-xs space-y-3">
        <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
          <Scale className="w-4 h-4 text-blue-600" />
          <span>Executive Summary</span>
        </h3>
        <p className="text-xs text-[var(--text-muted)] leading-relaxed font-normal">
          {analysis?.executive_summary || 'Loading executive synthesis...'}
        </p>
        <div className="pt-2 flex flex-wrap items-center gap-4 text-xs text-[var(--text-muted)] border-t border-[var(--border-color)]">
          <span>Analyzed Documents: <strong>{analysis?.document_count || 0}</strong></span>
          <span>Obligations Identified: <strong>{analysis?.obligations.length || 0}</strong></span>
          <span>Timeline Events: <strong>{analysis?.timeline.length || 0}</strong></span>
          <span>Evidence Findings: <strong>{analysis?.evidence_register.length || 0}</strong></span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-[var(--border-color)] flex items-center gap-6 text-xs font-bold">
        <button
          onClick={() => setActiveTab('obligations')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition-all ${
            activeTab === 'obligations'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]'
          }`}
        >
          <FileCheck className="w-4 h-4" />
          <span>Important Obligations ({analysis?.obligations.length || 0})</span>
        </button>

        <button
          onClick={() => setActiveTab('timeline')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition-all ${
            activeTab === 'timeline'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]'
          }`}
        >
          <Calendar className="w-4 h-4" />
          <span>Chronological Timeline ({analysis?.timeline.length || 0})</span>
        </button>

        <button
          onClick={() => setActiveTab('entities')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition-all ${
            activeTab === 'entities'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Parties & Entities ({analysis?.parties_and_entities.length || 0})</span>
        </button>

        <button
          onClick={() => setActiveTab('risks')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition-all ${
            activeTab === 'risks'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]'
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          <span>Risks & Observations ({analysis?.risks_and_observations.length || 0})</span>
        </button>

        <button
          onClick={() => setActiveTab('evidence')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition-all ${
            activeTab === 'evidence'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]'
          }`}
        >
          <Shield className="w-4 h-4" />
          <span>Evidence Register ({analysis?.evidence_register.length || 0})</span>
        </button>
      </div>

      {/* Tab Panes */}
      <div className="space-y-4">
        {/* Tab 1: Obligations */}
        {activeTab === 'obligations' && (
          <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[var(--bg-input)]/50 border-b border-[var(--border-color)] text-[var(--text-muted)] uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="py-3 px-4">Ref ID</th>
                    <th className="py-3 px-3">Responsible Party</th>
                    <th className="py-3 px-4">Obligation Specification</th>
                    <th className="py-3 px-3">Deadline / Interval</th>
                    <th className="py-3 px-4">Source Reference</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-color)]">
                  {analysis?.obligations.map((obl) => (
                    <tr key={obl.obligation_id} className="hover:bg-[var(--bg-input)]/30 transition-colors">
                      <td className="py-3 px-4 font-mono text-[10px] text-blue-600 font-semibold">
                        {obl.obligation_id}
                      </td>
                      <td className="py-3 px-3 font-semibold text-[var(--text-primary)]">
                        {obl.responsible_party}
                      </td>
                      <td className="py-3 px-4 text-[var(--text-primary)] max-w-md leading-relaxed">
                        “{obl.obligation_text}”
                      </td>
                      <td className="py-3 px-3 text-[var(--text-muted)] font-medium">
                        {obl.deadline_or_frequency}
                      </td>
                      <td className="py-3 px-4 text-[var(--text-muted)] font-mono text-[11px]">
                        {obl.source_document} (p. {obl.page_number})
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 2: Chronological Timeline */}
        {activeTab === 'timeline' && (
          <div className="p-6 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-xs space-y-6">
            <div className="relative border-l-2 border-blue-500/30 ml-4 pl-6 space-y-6">
              {analysis?.timeline.map((evt, idx) => (
                <div key={evt.event_id || idx} className="relative group">
                  <div className="absolute -left-[31px] top-1.5 w-3.5 h-3.5 rounded-full bg-blue-600 ring-4 ring-blue-100 dark:ring-blue-950" />
                  <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-input)]/20 hover:border-blue-400 transition-colors space-y-1.5 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-[var(--text-primary)]">{evt.date_str}</span>
                      <span className="text-[10px] font-mono text-[var(--text-muted)]">
                        {evt.source_document} · Page {evt.page_number}
                      </span>
                    </div>
                    <p className="text-[var(--text-muted)] leading-relaxed italic">
                      “{evt.description}”
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 3: Parties & Entities */}
        {activeTab === 'entities' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {analysis?.parties_and_entities.map((ent, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-2 text-xs shadow-2xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sm text-[var(--text-primary)]">{ent.name}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400">
                    {ent.category}
                  </span>
                </div>
                <p className="text-[11px] text-[var(--text-muted)]">
                  Mentioned {ent.mention_count} time(s) across {ent.source_documents.join(', ')}
                </p>
                <div className="p-2 rounded bg-[var(--bg-input)] font-mono text-[10px] text-[var(--text-muted)] truncate">
                  Context: {ent.sample_context}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tab 4: Risks & Observations */}
        {activeTab === 'risks' && (
          <div className="space-y-4">
            {analysis?.risks_and_observations.map((risk) => (
              <div
                key={risk.risk_id}
                className="p-5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-3 text-xs shadow-2xs"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className={`w-4 h-4 ${
                      risk.severity === 'high' ? 'text-red-500' : 'text-amber-500'
                    }`} />
                    <span className="font-bold text-sm text-[var(--text-primary)]">{risk.title}</span>
                  </div>
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                    risk.severity === 'high'
                      ? 'bg-red-500/15 text-red-600 dark:text-red-400'
                      : 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
                  }`}>
                    {risk.severity} Severity
                  </span>
                </div>
                <p className="text-[var(--text-muted)] leading-relaxed">{risk.description}</p>
                <div className="p-3 rounded-lg bg-[var(--bg-input)] border border-[var(--border-color)] text-[11px] space-y-1">
                  <span className="font-semibold text-[var(--text-primary)]">Recommendation:</span>
                  <p className="text-[var(--text-muted)]">{risk.recommendation}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tab 5: Evidence Register */}
        {activeTab === 'evidence' && (
          <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[var(--bg-input)]/50 border-b border-[var(--border-color)] text-[var(--text-muted)] uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="py-3 px-4">Finding ID</th>
                    <th className="py-3 px-4">Claim / Observation</th>
                    <th className="py-3 px-3">Source Document</th>
                    <th className="py-3 px-2">Page</th>
                    <th className="py-3 px-4 text-right">Verification Result</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-color)]">
                  {analysis?.evidence_register.map((ev) => (
                    <tr key={ev.finding_id} className="hover:bg-[var(--bg-input)]/30 transition-colors">
                      <td className="py-3 px-4 font-mono text-[10px] text-blue-600 font-semibold">
                        {ev.finding_id}
                      </td>
                      <td className="py-3 px-4 font-medium text-[var(--text-primary)] max-w-sm">
                        {ev.claim_or_observation}
                      </td>
                      <td className="py-3 px-3 text-[var(--text-muted)]">{ev.source_document}</td>
                      <td className="py-3 px-2 text-[var(--text-muted)]">p. {ev.page_number}</td>
                      <td className="py-3 px-4 text-right">
                        <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-semibold text-[10px] inline-flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          {ev.verification_result}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
