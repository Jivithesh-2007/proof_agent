import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Analysis } from '../types';
import { getAnalysisById } from '../services/analysis';
import { ResultCard } from '../components/analysis/ResultCard';
import { KPIGrid } from '../components/analysis/KPIGrid';
import { ExplanationCard } from '../components/analysis/ExplanationCard';
import { RuleReasoningPanel } from '../components/analysis/RuleReasoningPanel';
import { GroupedTableResult } from '../components/analysis/GroupedTableResult';
import { ProofTabs } from '../components/analysis/ProofTabs';
import { RefusalCard } from '../components/analysis/RefusalCard';
import { ConflictCard } from '../components/analysis/ConflictCard';
import { Button } from '../components/common/Button';
import { ArrowLeft, ShieldCheck, Check, AlertCircle, RefreshCw } from 'lucide-react';

export const AnalysisResultPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      setLoading(true);
      getAnalysisById(id).then((res) => {
        setAnalysis(res || null);
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, [id]);

  if (loading) {
    return (
      <div className="p-16 text-center space-y-4 font-mono">
        <div className="w-10 h-10 border-2 border-[#E64A32] border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-sm theme-text-muted">Loading verified analysis proof...</p>
      </div>
    );
  }

  // Unknown Analysis ID Handler (Phase 23)
  if (!analysis) {
    return (
      <div className="max-w-xl mx-auto p-12 text-center space-y-6 border theme-border rounded-xl theme-card my-12">
        <div className="w-14 h-14 rounded-2xl bg-[#E64A32]/15 border border-[#E64A32]/30 flex items-center justify-center text-[#E64A32] mx-auto">
          <AlertCircle className="w-7 h-7" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-bold">Analysis Not Found</h2>
          <p className="text-sm theme-text-muted">
            The requested analysis ID <span className="font-mono text-[#E64A32]">"{id}"</span> does not exist in backend storage.
          </p>
        </div>
        <Button variant="primary" onClick={() => navigate('/analysis')}>
          <ArrowLeft className="w-4 h-4" /> Go to Analysis Workspace
        </Button>
      </div>
    );
  }

  const isRefusal = analysis.status === 'refused';
  const isConflict = !!analysis.conflictDetails;
  const isGroupedTable = Array.isArray(analysis.tableData) && analysis.tableData.length > 0;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Top Breadcrumb & Question */}
      <div className="space-y-3 border-b theme-border pb-6">
        <Button variant="ghost" size="sm" onClick={() => navigate('/analysis')} className="theme-text-muted">
          <ArrowLeft className="w-4 h-4" /> Back to Workspace
        </Button>

        <div>
          <span className="text-xs uppercase font-semibold theme-text-muted tracking-wider">
            Analysis Result & Verification Certificate
          </span>
          <h1 className="text-2xl md:text-3xl font-bold mt-1">{analysis.question}</h1>
        </div>
      </div>

      {/* Render Refusal State */}
      {isRefusal ? (
        <div className="space-y-6">
          <RuleReasoningPanel analysis={analysis} />
          <RefusalCard analysis={analysis} />
        </div>
      ) : isConflict ? (
        <div className="space-y-6">
          <RuleReasoningPanel analysis={analysis} />
          <ConflictCard analysis={analysis} />
        </div>
      ) : (
        <>
          {/* Dominant Answer Card */}
          <ResultCard analysis={analysis} />

          {/* ProofAI Rule Reasoning Panel (Phase 25) */}
          <RuleReasoningPanel analysis={analysis} />

          {/* Grouped Table Visualizer if Group Results Exist (Phase 26) */}
          {isGroupedTable && (
            <GroupedTableResult
              data={analysis.tableData!}
              metric={analysis.canonicalResult?.metric}
              unit={analysis.canonicalResult?.unit}
            />
          )}

          {/* KPI Summary Row */}
          {analysis.kpis && analysis.kpis.length > 0 && <KPIGrid kpis={analysis.kpis} />}

          {/* Explanation Step-by-Step */}
          <ExplanationCard explanation={analysis.explanation} />

          {/* Proof Tabs */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold theme-text-muted uppercase tracking-wider">
              Verification Proof & Audit Tabs
            </h3>
            <ProofTabs analysis={analysis} />
          </div>

          {/* Confidence Indicator Section */}
          <div className="theme-card border theme-border rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b theme-border pb-3">
              <h3 className="text-base font-bold flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-[#E64A32]" /> Proof Policy & Verification Audit
              </h3>
              <span className="px-3 py-1 rounded-full text-xs font-bold uppercase bg-[#E64A32]/20 text-[#E64A32] border border-[#E64A32]/30">
                {analysis.status === 'verified' ? 'VERIFIED' : analysis.status.toUpperCase()}
              </span>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="theme-text-muted uppercase font-sans font-semibold tracking-wider text-[11px] mb-2">
                Verification Proof Checklist:
              </div>
              {analysis.verification?.confidenceReason.map((reason, idx) => (
                <div key={idx} className="flex items-center gap-2 theme-input p-2.5 rounded border theme-border">
                  <Check className="w-4 h-4 text-[#E64A32] shrink-0" />
                  <span>{reason}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
