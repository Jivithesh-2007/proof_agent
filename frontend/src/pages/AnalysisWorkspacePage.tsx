import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Dataset } from '../types';
import { getDatasets } from '../services/datasets';
import { QuestionInput } from '../components/analysis/QuestionInput';
import { SuggestedQuestions } from '../components/analysis/SuggestedQuestions';
import { createAnalysis } from '../services/analysis';
import { Database, Layers, Columns, ShieldCheck, AlertCircle, Sparkles, CheckCircle2 } from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';

export const AnalysisWorkspacePage: React.FC = () => {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [question, setQuestion] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    getDatasets().then((data) => {
      setDatasets(data);
      if (data.length > 0) {
        setSelectedDataset(data[0]);
      }
    });
  }, []);

  const handleRun = async () => {
    if (!question.trim()) return;
    setIsProcessing(true);
    setErrorMessage(null);

    try {
      const dsId = selectedDataset?.id || '';
      const dsName = selectedDataset?.name || 'dataset.csv';
      const analysis = await createAnalysis(question, dsId, dsName);
      setIsProcessing(false);
      navigate(`/analysis/${analysis.id}`);
    } catch (err: any) {
      setIsProcessing(false);
      setErrorMessage(err.message || 'Failed to execute analysis. Please verify backend connectivity.');
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Page Title */}
      <div className="border-b theme-border pb-4">
        <h1 className="text-2xl font-bold tracking-tight">Analysis Workspace</h1>
        <p className="text-sm theme-text-muted mt-1">
          Formulate analytical queries. ProofAI Rule Analyst deterministically evaluates schemas and verifies answers.
        </p>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-xl bg-[#E64A32]/15 border border-[#E64A32]/40 text-[#E64A32] flex items-center gap-3 text-sm font-mono">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {isProcessing ? (
        <div className="max-w-xl mx-auto p-12 text-center space-y-6 border theme-border rounded-xl theme-card my-12 shadow-xl">
          <div className="w-14 h-14 rounded-2xl bg-[#E64A32]/15 border border-[#E64A32]/30 flex items-center justify-center text-[#E64A32] mx-auto animate-pulse">
            <ShieldCheck className="w-7 h-7 animate-spin" />
          </div>
          <div className="space-y-2 font-mono">
            <h3 className="text-lg font-bold text-[#F4F5EC]">Executing ProofAI Verification Pipeline</h3>
            <p className="text-xs text-[#F4F5EC]/60">
              Profiling schema ➔ Applying Rule Analyst ➔ Validating Contract ➔ Executing Analytics ➔ Verifying Proof
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          {/* Left Panel: Active Dataset Context */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold theme-text-muted uppercase tracking-wider">
                Active Dataset Context
              </h3>
              <span className="text-[11px] font-mono text-[#E64A32]">
                {datasets.length} Available
              </span>
            </div>

            {selectedDataset ? (
              <Card className="space-y-4">
                <div className="flex items-center gap-3 border-b theme-border pb-3">
                  <div className="w-10 h-10 rounded-lg bg-[#E64A32]/15 border border-[#E64A32]/30 flex items-center justify-center text-[#E64A32]">
                    <Database className="w-5 h-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h4 className="text-sm font-bold font-mono truncate">{selectedDataset.name}</h4>
                    <span className="text-[11px] font-mono text-[#E64A32] flex items-center gap-1 font-semibold">
                      <ShieldCheck className="w-3 h-3" /> Ready for verification
                    </span>
                  </div>
                </div>

                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between theme-text-muted py-1 border-b theme-border">
                    <span className="flex items-center gap-1.5 font-sans">
                      <Layers className="w-3.5 h-3.5" /> Total Rows
                    </span>
                    <span className="font-bold text-[#F4F5EC]">{selectedDataset.rows.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between theme-text-muted py-1 border-b theme-border">
                    <span className="flex items-center gap-1.5 font-sans">
                      <Columns className="w-3.5 h-3.5" /> Columns ({selectedDataset.columns})
                    </span>
                    <span className="font-bold text-[#F4F5EC] truncate max-w-[140px]" title={selectedDataset.columnNames.join(', ')}>
                      {selectedDataset.columnNames.slice(0, 3).join(', ')}...
                    </span>
                  </div>
                  {selectedDataset.sha256 && (
                    <div className="flex justify-between theme-text-muted py-1">
                      <span className="font-sans">SHA-256</span>
                      <span className="text-[#E64A32] font-mono font-semibold truncate max-w-[120px]">
                        {selectedDataset.sha256.substring(0, 10)}...
                      </span>
                    </div>
                  )}
                </div>

                {/* Dataset switcher dropdown if multiple datasets exist */}
                {datasets.length > 1 && (
                  <div className="pt-2 border-t theme-border">
                    <label className="text-[11px] font-sans font-semibold theme-text-muted block mb-1">
                      Switch Active Dataset:
                    </label>
                    <select
                      value={selectedDataset.id}
                      onChange={(e) => {
                        const ds = datasets.find((d) => d.id === e.target.value);
                        if (ds) setSelectedDataset(ds);
                      }}
                      className="w-full text-xs font-mono theme-input p-2 rounded-lg border theme-border"
                    >
                      {datasets.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name} ({d.rows} rows)
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </Card>
            ) : (
              <Card className="p-6 text-center space-y-3">
                <AlertCircle className="w-8 h-8 text-[#E18230] mx-auto" />
                <p className="text-xs theme-text-muted">No datasets uploaded yet.</p>
                <Button size="sm" variant="primary" onClick={() => navigate('/data')}>
                  Upload Dataset
                </Button>
              </Card>
            )}

            <div className="theme-card border theme-border rounded-xl p-4 text-xs leading-relaxed space-y-2">
              <div className="font-bold uppercase tracking-wider text-[11px] text-[#E18230]">
                ProofAI Deterministic Pipeline
              </div>
              <p className="theme-text-muted">• Dynamic schema inspection & normalization</p>
              <p className="theme-text-muted">• ProofAI Rule Analyst formulates deterministic contract</p>
              <p className="theme-text-muted">• Contract executed in isolated sandbox</p>
              <p className="theme-text-muted">• Independent Reference Engine verifies result</p>
              <p className="theme-text-muted">• Unresolvable columns or concepts are strictly refused</p>
            </div>
          </div>

          {/* Right Panel: Ask ProofAI */}
          <div className="lg:col-span-2 space-y-6">
            <div className="space-y-2">
              <h3 className="text-xs font-semibold theme-text-muted uppercase tracking-wider">
                Ask ProofAI
              </h3>
              <QuestionInput
                question={question}
                onChange={setQuestion}
                onSubmit={handleRun}
                loading={isProcessing}
              />
            </div>

            <SuggestedQuestions onSelect={(q) => setQuestion(q)} />
          </div>
        </div>
      )}
    </div>
  );
};
