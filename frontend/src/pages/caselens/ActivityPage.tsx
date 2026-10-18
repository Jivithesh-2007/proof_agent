import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  Activity,
  FileText,
  MessageSquare,
  Scale,
  AlertTriangle,
  FileCheck,
  Clock,
  CheckCircle2,
  Filter,
} from 'lucide-react';
import { caselensApi } from '../../services/caselensApi';
import { QuestionAnswerResponse, DocumentMetadata, ReportExportResponse } from '../../types/caselens';

export const ActivityPage: React.FC = () => {
  const { currentWs } = useOutletContext<{ currentWs: string }>();

  const [qaRuns, setQaRuns] = useState<QuestionAnswerResponse[]>([]);
  const [docs, setDocs] = useState<DocumentMetadata[]>([]);
  const [reports, setReports] = useState<ReportExportResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadActivity();
  }, [currentWs]);

  const loadActivity = async () => {
    setLoading(true);
    try {
      const [history, docList, reportList] = await Promise.all([
        caselensApi.getQAHistory(currentWs),
        caselensApi.listDocuments(currentWs),
        caselensApi.listReports(currentWs),
      ]);
      setQaRuns(history);
      setDocs(docList);
      setReports(reportList);
    } catch (e) {
      console.error('Failed to load activity', e);
    } finally {
      setLoading(false);
    }
  };

  // Merge into chronological activity stream
  const activities = [
    ...qaRuns.map(q => ({
      type: 'qa',
      title: `Query: “${q.question}”`,
      subtitle: q.has_sufficient_evidence
        ? `Answered with ${q.citations.length} citation(s) · Verified`
        : 'Insufficient evidence honest refusal',
      timestamp: q.created_at,
      icon: MessageSquare,
      color: q.has_sufficient_evidence ? 'blue' : 'amber',
    })),
    ...docs.map(d => ({
      type: 'upload',
      title: `Document Ingested: ${d.filename}`,
      subtitle: `${d.file_type.toUpperCase()} · ${d.page_count} pages · ${d.chunk_count} chunks · SHA: ${d.content_hash.substring(0, 10)}...`,
      timestamp: d.created_at,
      icon: FileText,
      color: 'emerald',
    })),
    ...reports.map(r => ({
      type: 'report',
      title: `Report Compiled: ${r.title}`,
      subtitle: `${r.findings_count} findings across ${r.documents_analyzed.length} documents`,
      timestamp: r.created_at,
      icon: FileCheck,
      color: 'purple',
    })),
  ].sort((a, b) => (b.timestamp > a.timestamp ? 1 : -1));

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-600/10 text-blue-600 dark:text-blue-400">
            Immutable Audit Trail
          </span>
          <span className="text-xs text-[var(--text-muted)]">Provenance Tracking</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
          Workspace Activity & Audit Log
        </h1>
        <p className="text-xs text-[var(--text-muted)] mt-1">
          Complete log of queries asked, documents indexed, contradictions detected, and intelligence reports exported.
        </p>
      </div>

      {/* Activity Timeline List */}
      <div className="p-6 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-xs space-y-6">
        <div className="relative border-l-2 border-[var(--border-color)] ml-4 pl-6 space-y-6">
          {activities.length === 0 ? (
            <div className="p-8 text-center text-xs text-[var(--text-muted)]">
              No activity recorded in this workspace yet.
            </div>
          ) : (
            activities.map((act, idx) => {
              const Icon = act.icon;
              return (
                <div key={idx} className="relative group">
                  <div className={`absolute -left-[31px] top-1.5 w-3.5 h-3.5 rounded-full ring-4 ring-[var(--bg-card)] ${
                    act.color === 'blue'
                      ? 'bg-blue-600'
                      : act.color === 'emerald'
                      ? 'bg-emerald-600'
                      : act.color === 'amber'
                      ? 'bg-amber-500'
                      : 'bg-purple-600'
                  }`} />
                  <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-input)]/20 hover:border-blue-400 transition-colors space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-[var(--text-primary)] flex items-center gap-2">
                        <Icon className="w-4 h-4 text-blue-600" />
                        <span>{act.title}</span>
                      </span>
                      <span className="text-[10px] font-mono text-[var(--text-muted)]">
                        {act.timestamp.substring(0, 19).replace('T', ' ')}
                      </span>
                    </div>
                    <p className="text-[var(--text-muted)] leading-relaxed">
                      {act.subtitle}
                    </p>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
