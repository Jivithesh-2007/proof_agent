import React from 'react';
import { Analysis } from '../../types';
import { Cpu, CheckCircle2, ShieldCheck, FileText, ArrowRight } from 'lucide-react';

interface RuleReasoningPanelProps {
  analysis: Analysis;
}

export const RuleReasoningPanel: React.FC<RuleReasoningPanelProps> = ({ analysis }) => {
  const rules = analysis.ruleReasoning || [];
  const contract = analysis.analysisContract || {};

  return (
    <div className="bg-[#242726] border border-[#E64A32]/30 rounded-xl p-6 shadow-lg space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#3C3B39] pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#E64A32]/15 border border-[#E64A32]/30 flex items-center justify-center text-[#E64A32]">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-[#F4F5EC] flex items-center gap-2">
              ProofAI Rule Reasoning & Deterministic Contract
            </h3>
            <p className="text-xs text-[#F4F5EC]/60">
              Natural language analytical reasoning mapped through deterministic IF–THEN rules (Zero LLM)
            </p>
          </div>
        </div>

        <span className="px-3 py-1 rounded-full text-xs font-mono font-bold uppercase bg-[#E64A32]/20 text-[#E64A32] border border-[#E64A32]/40">
          Deterministic Engine
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Matched IF-THEN Rules */}
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-[#E18230] uppercase tracking-wider flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" /> Matched Analytical Rules
          </h4>

          {rules.length > 0 ? (
            <div className="space-y-2 font-mono text-xs">
              {rules.map((rule, idx) => (
                <div
                  key={idx}
                  className="bg-[#151918] border border-[#3C3B39] rounded-lg p-3 text-[#F4F5EC] flex items-start gap-2"
                >
                  <span className="text-[#E64A32] font-bold">[{idx + 1}]</span>
                  <span>{rule}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-[#151918] border border-[#3C3B39] rounded-lg p-4 text-xs text-[#F4F5EC]/60 font-mono">
              Standard analytical contract synthesis applied.
            </div>
          )}
        </div>

        {/* Right: Synthesized Analysis Contract */}
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-[#E64A32] uppercase tracking-wider flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5" /> Synthesized Analysis Contract
          </h4>

          <div className="bg-[#151918] border border-[#3C3B39] rounded-lg p-4 font-mono text-xs text-[#F4F5EC] space-y-2 overflow-x-auto">
            <div className="flex justify-between border-b border-[#3C3B39]/60 pb-1.5">
              <span className="text-[#F4F5EC]/60">Query Intent:</span>
              <span className="font-bold text-[#E18230]">{contract.query_type || 'data_aggregation'}</span>
            </div>
            <div className="flex justify-between border-b border-[#3C3B39]/60 pb-1.5">
              <span className="text-[#F4F5EC]/60">Dataset:</span>
              <span className="text-[#F4F5EC]">{contract.datasets_required?.[0] || analysis.datasetId}</span>
            </div>
            <div className="flex justify-between border-b border-[#3C3B39]/60 pb-1.5">
              <span className="text-[#F4F5EC]/60">Expected Result Type:</span>
              <span className="text-[#E64A32] font-bold">{contract.expected_result_type || 'scalar'}</span>
            </div>
            {contract.aggregations && contract.aggregations.length > 0 && (
              <div className="flex justify-between border-b border-[#3C3B39]/60 pb-1.5">
                <span className="text-[#F4F5EC]/60">Aggregation:</span>
                <span className="text-[#F4F5EC]">{contract.aggregations[0].operation}({contract.aggregations[0].column || '*'})</span>
              </div>
            )}
            {contract.group_by && contract.group_by.length > 0 && (
              <div className="flex justify-between border-b border-[#3C3B39]/60 pb-1.5">
                <span className="text-[#F4F5EC]/60">Group By:</span>
                <span className="text-[#E18230] font-bold">{contract.group_by.map((g: any) => g.column || g).join(', ')}</span>
              </div>
            )}
            {contract.filters && contract.filters.length > 0 && (
              <div className="flex justify-between border-b border-[#3C3B39]/60 pb-1.5">
                <span className="text-[#F4F5EC]/60">Filters:</span>
                <span className="text-[#F4F5EC]">{contract.filters.map((f: any) => `${f.column} ${f.operator} ${f.value}`).join(', ')}</span>
              </div>
            )}
            {contract.sorting && contract.sorting.length > 0 && (
              <div className="flex justify-between border-b border-[#3C3B39]/60 pb-1.5">
                <span className="text-[#F4F5EC]/60">Sorting:</span>
                <span className="text-[#F4F5EC]">{contract.sorting[0].column} ({contract.sorting[0].order})</span>
              </div>
            )}
            <div className="flex justify-between pt-1">
              <span className="text-[#F4F5EC]/60">Unit:</span>
              <span className="text-[#F4F5EC]">{contract.expected_unit || 'unverified (none)'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
