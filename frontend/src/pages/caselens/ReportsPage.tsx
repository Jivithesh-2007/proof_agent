import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  FileCheck,
  Download,
  Share2,
  Printer,
  Sparkles,
  Clock,
  CheckCircle2,
  AlertTriangle,
  FileText,
  RefreshCw,
  Copy,
  Check,
} from 'lucide-react';
import { caselensApi } from '../../services/caselensApi';
import { ReportExportResponse } from '../../types/caselens';

export const ReportsPage: React.FC = () => {
  const { currentWs } = useOutletContext<{ currentWs: string }>();

  const [reports, setReports] = useState<ReportExportResponse[]>([]);
  const [activeReport, setActiveReport] = useState<ReportExportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadReports();
  }, [currentWs]);

  const loadReports = async () => {
    setLoading(true);
    try {
      const list = await caselensApi.listReports(currentWs);
      setReports(list);
      if (list.length > 0) {
        setActiveReport(list[0]);
      } else {
        // Automatically create initial report if none exist
        await handleGenerate();
      }
    } catch (e) {
      console.error('Failed to load reports', e);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const newRpt = await caselensApi.createReport(currentWs);
      setActiveReport(newRpt);
      setReports(prev => [newRpt, ...prev]);
    } catch (e) {
      alert('Report generation failed: ' + e);
    } finally {
      setGenerating(false);
    }
  };

  const handleCopyMarkdown = () => {
    if (!activeReport) return;
    navigator.clipboard.writeText(activeReport.markdown_content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!activeReport) return;
    const blob = new Blob([activeReport.markdown_content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `CaseLens_${activeReport.report_id}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-purple-500/15 text-purple-600 dark:text-purple-400">
              Audit-Grade Report Center
            </span>
            <span className="text-xs text-[var(--text-muted)] font-mono">{activeReport?.report_id}</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
            Intelligence Reports & Evidence Dossiers
          </h1>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Comprehensive audit reports compiling executive summaries, cross-document contradictions, and verified evidence registers.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs flex items-center gap-2 transition-all disabled:opacity-50"
          >
            <Sparkles className={`w-3.5 h-3.5 ${generating ? 'animate-spin' : ''}`} />
            <span>{generating ? 'Compiling Report...' : 'Generate New Report'}</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Left selector + Right Viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Report History List */}
        <div className="lg:col-span-4 space-y-3">
          <h3 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">
            Available Reports ({reports.length})
          </h3>
          <div className="space-y-2">
            {reports.map((rpt) => (
              <div
                key={rpt.report_id}
                onClick={() => setActiveReport(rpt)}
                className={`p-4 rounded-xl border cursor-pointer transition-all space-y-1.5 ${
                  activeReport?.report_id === rpt.report_id
                    ? 'border-blue-600 bg-blue-50/40 dark:bg-blue-950/30 shadow-xs'
                    : 'border-[var(--border-color)] bg-[var(--bg-card)] hover:bg-[var(--bg-input)]/40'
                }`}
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[var(--text-primary)] truncate max-w-[200px]">
                    {rpt.title}
                  </span>
                  <span className="text-[10px] font-mono text-[var(--text-muted)]">
                    {rpt.report_id}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-[11px] text-[var(--text-muted)]">
                  <span>{rpt.documents_analyzed.length} doc(s)</span>
                  <span>·</span>
                  <span>{rpt.findings_count} finding(s)</span>
                  <span>·</span>
                  <span>{rpt.created_at.substring(0, 10)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Active Report Reader */}
        <div className="lg:col-span-8 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-xs flex flex-col overflow-hidden">
          {/* Action Toolbar */}
          <div className="p-4 border-b border-[var(--border-color)] bg-[var(--bg-input)]/40 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-bold text-[var(--text-primary)]">
                {activeReport?.title || 'Report Reader'}
              </h2>
              <p className="text-[11px] text-[var(--text-muted)] font-mono">
                Generated {activeReport?.created_at}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleCopyMarkdown}
                className="px-3 py-1.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] hover:bg-[var(--bg-input)] text-xs font-semibold text-[var(--text-primary)] flex items-center gap-1.5 transition-colors"
                title="Copy raw Markdown"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied!' : 'Copy Markdown'}</span>
              </button>

              <button
                onClick={handleDownload}
                className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-2xs transition-colors"
                title="Download as .md file"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download Report</span>
              </button>

              <button
                onClick={handlePrint}
                className="p-1.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] hover:bg-[var(--bg-input)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                title="Print Report"
              >
                <Printer className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Report Markdown Viewer Body */}
          <div className="p-8 overflow-y-auto max-h-[75vh] space-y-6 font-sans text-xs leading-relaxed">
            {activeReport ? (
              <div className="prose dark:prose-invert max-w-none space-y-4">
                <div className="p-4 rounded-xl bg-[var(--bg-input)]/30 border border-[var(--border-color)] space-y-1">
                  <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
                    Executive Brief
                  </span>
                  <p className="text-xs text-[var(--text-primary)] font-medium leading-relaxed">
                    {activeReport.executive_summary}
                  </p>
                </div>

                <div className="border-t border-[var(--border-color)] pt-4 space-y-2">
                  <h4 className="font-bold text-sm text-[var(--text-primary)]">
                    Analyzed Documents in Portfolio
                  </h4>
                  <ul className="list-disc list-inside space-y-1 text-[var(--text-muted)]">
                    {activeReport.documents_analyzed.map((docName, idx) => (
                      <li key={idx} className="font-mono text-[11px] text-[var(--text-primary)]">
                        {docName}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Preformatted Markdown Document Display */}
                <div className="border-t border-[var(--border-color)] pt-4">
                  <h4 className="font-bold text-sm text-[var(--text-primary)] mb-2">
                    Complete Compiled Markdown Dossier
                  </h4>
                  <pre className="p-4 rounded-xl bg-[var(--bg-input)] font-mono text-[11px] text-[var(--text-primary)] overflow-x-auto whitespace-pre-wrap leading-relaxed border border-[var(--border-color)]">
                    {activeReport.markdown_content}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="p-12 text-center text-[var(--text-muted)]">
                No report selected.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
