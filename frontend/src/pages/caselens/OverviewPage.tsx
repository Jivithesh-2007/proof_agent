import React, { useEffect, useState } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import {
  FileText,
  AlertTriangle,
  FileCheck,
  Scale,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Layers,
  Search,
  GitCompare,
  FileQuestion,
  RotateCcw,
} from 'lucide-react';
import { caselensApi } from '../../services/caselensApi';
import { DocumentMetadata, CaseAnalysisResponse, ContradictionResponse } from '../../types/caselens';

export const OverviewPage: React.FC = () => {
  const navigate = useNavigate();
  const { currentWs } = useOutletContext<{ currentWs: string }>();

  const [docs, setDocs] = useState<DocumentMetadata[]>([]);
  const [analysis, setAnalysis] = useState<CaseAnalysisResponse | null>(null);
  const [contradictions, setContradictions] = useState<ContradictionResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [currentWs]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [docList, analysisData, contraData] = await Promise.all([
        caselensApi.listDocuments(currentWs),
        caselensApi.getCaseAnalysis(currentWs).catch(() => null),
        caselensApi.getContradictions(currentWs).catch(() => null),
      ]);
      setDocs(docList);
      setAnalysis(analysisData);
      setContradictions(contraData);
    } catch (e) {
      console.error('Error loading overview data', e);
    } finally {
      setLoading(false);
    }
  };

  const totalPages = docs.reduce((acc, d) => acc + d.page_count, 0);
  const totalChunks = docs.reduce((acc, d) => acc + d.chunk_count, 0);

  const demoScenarios = [
    {
      id: 1,
      title: 'Supported Legal Q&A',
      desc: 'Query payment terms and obligations with exact bracketed citations.',
      action: () => navigate('/caselens/ask?q=What is the base retainer fee and SLA obligation?'),
      tag: 'Scenario 1',
      color: 'blue',
      icon: Sparkles,
    },
    {
      id: 2,
      title: 'Evidence Refusal (Zero Hallucination)',
      desc: 'Ask an unsupported query and verify honest refusal response.',
      action: () => navigate('/caselens/ask?q=What are the nuclear export tariffs?'),
      tag: 'Scenario 2',
      color: 'slate',
      icon: ShieldCheck,
    },
    {
      id: 3,
      title: 'Conflicting Expiration Dates',
      desc: 'Inspect June 30, 2027 vs July 31, 2027 discrepancy side-by-side.',
      action: () => navigate('/caselens/contradictions'),
      tag: 'Scenario 3',
      color: 'amber',
      icon: AlertTriangle,
    },
    {
      id: 4,
      title: 'Fee Amount Comparison',
      desc: 'Compare $150,000 Master Agreement vs $225,000 Addendum.',
      action: () => navigate('/caselens/compare'),
      tag: 'Scenario 4',
      color: 'indigo',
      icon: GitCompare,
    },
    {
      id: 5,
      title: 'Missing Clause Checklist',
      desc: 'Audit warehouse lease for missing indemnification and force majeure.',
      action: () => navigate('/caselens/missing-info'),
      tag: 'Scenario 5',
      color: 'emerald',
      icon: FileQuestion,
    },
    {
      id: 6,
      title: 'Full Audit Intelligence Report',
      desc: 'View synthesized executive summary, timeline, and evidence register.',
      action: () => navigate('/caselens/reports'),
      tag: 'Scenario 6',
      color: 'purple',
      icon: FileCheck,
    },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-12">
      {/* Welcome Banner */}
      <div className="p-6 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-xs relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-600/10 text-blue-600 dark:text-blue-400">
                Workspace Dashboard
              </span>
              <span className="text-xs text-[var(--text-muted)] flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" /> Project Meridian
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
              Document Intelligence & Verification
            </h1>
            <p className="text-xs text-[var(--text-muted)] mt-1 max-w-2xl">
              Deterministic extraction active. Every claim in this workspace is linked to exact source coordinates,
              enabling transparent provenance verification without model hallucination.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/caselens/ask')}
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs flex items-center gap-2 transition-all"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Ask Question</span>
            </button>
            <button
              onClick={() => navigate('/caselens/documents')}
              className="px-4 py-2 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] hover:bg-[var(--bg-input)] text-xs font-semibold text-[var(--text-primary)] transition-all"
            >
              Upload Document
            </button>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-1">
          <div className="flex items-center justify-between text-[var(--text-muted)] text-xs">
            <span>Documents Analyzed</span>
            <FileText className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-[var(--text-primary)]">{docs.length}</p>
          <p className="text-[11px] text-[var(--text-muted)]">{totalPages} total pages indexed</p>
        </div>

        <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-1">
          <div className="flex items-center justify-between text-[var(--text-muted)] text-xs">
            <span>Extracted Chunks</span>
            <Layers className="w-4 h-4 text-indigo-600" />
          </div>
          <p className="text-2xl font-bold text-[var(--text-primary)]">{totalChunks}</p>
          <p className="text-[11px] text-[var(--text-muted)]">Character offsets preserved</p>
        </div>

        <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-1">
          <div className="flex items-center justify-between text-[var(--text-muted)] text-xs">
            <span>Contradictions</span>
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">
            {contradictions ? contradictions.total_contradictions : 0}
          </p>
          <p className="text-[11px] text-[var(--text-muted)]">Cross-document conflicts</p>
        </div>

        <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-1">
          <div className="flex items-center justify-between text-[var(--text-muted)] text-xs">
            <span>Obligations Found</span>
            <Scale className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
            {analysis ? analysis.obligations.length : 0}
          </p>
          <p className="text-[11px] text-[var(--text-muted)]">Duty & deadline citations</p>
        </div>
      </div>

      {/* 6 Curated Demonstration Scenarios */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-[var(--text-primary)]">
              Curated Demonstration Scenarios
            </h2>
            <p className="text-xs text-[var(--text-muted)]">
              Explore the required evaluation journeys with preloaded Project Meridian documents.
            </p>
          </div>
          <span className="text-xs font-semibold text-blue-600">Deterministic · No GPU Required</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {demoScenarios.map((sc) => {
            const Icon = sc.icon;
            return (
              <div
                key={sc.id}
                onClick={sc.action}
                className="p-5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] hover:border-blue-500 hover:shadow-md cursor-pointer transition-all space-y-3 group"
              >
                <div className="flex items-center justify-between">
                  <div className="w-8 h-8 rounded-lg bg-blue-600/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-[var(--bg-input)] text-[var(--text-muted)]">
                    {sc.tag}
                  </span>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[var(--text-primary)] group-hover:text-blue-600 transition-colors">
                    {sc.title}
                  </h3>
                  <p className="text-xs text-[var(--text-muted)] mt-1 leading-relaxed">
                    {sc.desc}
                  </p>
                </div>
                <div className="pt-1 flex items-center text-xs font-semibold text-blue-600 group-hover:translate-x-0.5 transition-transform">
                  <span>Launch Scenario</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1" />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Document Library Preview & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Document Library Table */}
        <div className="lg:col-span-8 p-5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-600" />
              <span>Workspace Document Library</span>
            </h3>
            <button
              onClick={() => navigate('/caselens/documents')}
              className="text-xs text-blue-600 hover:underline font-semibold"
            >
              View All ({docs.length}) →
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-[var(--border-color)] text-[var(--text-muted)] uppercase tracking-wider">
                <tr>
                  <th className="pb-2 font-medium">Filename</th>
                  <th className="pb-2 font-medium">Type</th>
                  <th className="pb-2 font-medium">Pages</th>
                  <th className="pb-2 font-medium">Status</th>
                  <th className="pb-2 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-color)]">
                {docs.slice(0, 4).map((d) => (
                  <tr key={d.document_id} className="hover:bg-[var(--bg-input)]/40 transition-colors">
                    <td className="py-2.5 font-medium text-[var(--text-primary)] max-w-[200px] truncate">
                      {d.filename}
                    </td>
                    <td className="py-2.5 text-[var(--text-muted)] uppercase">{d.file_type}</td>
                    <td className="py-2.5 text-[var(--text-muted)]">{d.page_count}</td>
                    <td className="py-2.5">
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 text-[10px] font-semibold">
                        {d.processing_status}
                      </span>
                    </td>
                    <td className="py-2.5 text-right">
                      <button
                        onClick={() => navigate(`/caselens/ask?doc=${d.document_id}`)}
                        className="text-blue-600 hover:underline font-semibold"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Executive Summary Card */}
        <div className="lg:col-span-4 p-5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-3 flex flex-col justify-between">
          <div className="space-y-2">
            <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
              <Scale className="w-4 h-4 text-blue-600" />
              <span>Executive Brief</span>
            </h3>
            <p className="text-xs text-[var(--text-muted)] leading-relaxed">
              {analysis?.executive_summary ||
                'CaseLens AI examined the loaded documents. The primary scope encompasses contractual agreements, service level obligations, and commercial exhibits.'}
            </p>
          </div>

          <div className="pt-4 border-t border-[var(--border-color)] space-y-2">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)]">
              <span>Verified Invariants:</span>
              <span className="font-semibold text-emerald-600">Strict Provenance</span>
            </div>
            <button
              onClick={() => navigate('/caselens/analysis')}
              className="w-full py-2 rounded-lg bg-[var(--bg-input)] hover:bg-[var(--bg-card)] border border-[var(--border-color)] text-xs font-semibold text-[var(--text-primary)] transition-colors text-center"
            >
              Open Comprehensive Analysis
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
