import React, { useState, useEffect } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import {
  Settings,
  Cpu,
  Database,
  Shield,
  RotateCcw,
  CheckCircle2,
  HardDrive,
  Lock,
  Layers,
  Sparkles,
  Info,
} from 'lucide-react';
import { caselensApi } from '../../services/caselensApi';
import { Workspace } from '../../types/caselens';

export const SettingsPage: React.FC = () => {
  const { currentWs, reloadWorkspaces } = useOutletContext<{ currentWs: string; reloadWorkspaces: () => Promise<void> }>();
  const navigate = useNavigate();

  const [ws, setWs] = useState<Workspace | null>(null);
  const [providerMode, setProviderMode] = useState<'deterministic' | 'ollama' | 'openai'>('deterministic');
  const [resetting, setResetting] = useState(false);
  const [healthStatus, setHealthStatus] = useState<any>(null);

  useEffect(() => {
    loadSettings();
  }, [currentWs]);

  const loadSettings = async () => {
    try {
      const [workspace, health] = await Promise.all([
        caselensApi.getWorkspace(currentWs).catch(() => null),
        caselensApi.checkHealth().catch(() => null),
      ]);
      setWs(workspace);
      setHealthStatus(health);
    } catch (e) {
      console.error('Failed to load settings', e);
    }
  };

  const handleResetDemo = async () => {
    if (!confirm('Are you sure you want to reset the sample workspace documents and runs?')) return;
    setResetting(true);
    try {
      await caselensApi.resetDemoWorkspace();
      await reloadWorkspaces();
      alert('Demo workspace reset to initial state successfully.');
      navigate('/caselens/overview');
    } catch (e) {
      alert('Reset failed: ' + e);
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-600/10 text-blue-600 dark:text-blue-400">
            System Configuration
          </span>
          <span className="text-xs text-[var(--text-muted)]">Local-First Architecture</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
          Workspace Settings & Model Provider Interface
        </h1>
        <p className="text-xs text-[var(--text-muted)] mt-1">
          Manage local SQLite storage, review transparent AI disclosures, and configure pluggable model endpoints.
        </p>
      </div>

      {/* Model Provider Interface & AI Disclosure */}
      <div className="p-6 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-xs space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[var(--border-color)]">
          <div className="flex items-center gap-2.5">
            <Cpu className="w-5 h-5 text-blue-600" />
            <div>
              <h3 className="font-bold text-sm text-[var(--text-primary)]">
                Inference Engine & Model Provider Interface
              </h3>
              <p className="text-[11px] text-[var(--text-muted)]">
                CaseLens AI never falsely claims an external LLM was used when deterministic extraction is active.
              </p>
            </div>
          </div>
          <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-semibold text-xs flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> Deterministic Active
          </span>
        </div>

        <div className="space-y-3">
          <div
            onClick={() => setProviderMode('deterministic')}
            className={`p-4 rounded-xl border cursor-pointer transition-all space-y-1.5 ${
              providerMode === 'deterministic'
                ? 'border-blue-600 bg-blue-50/40 dark:bg-blue-950/20'
                : 'border-[var(--border-color)] bg-[var(--bg-input)]/20'
            }`}
          >
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-[var(--text-primary)] flex items-center gap-2">
                <Shield className="w-4 h-4 text-blue-600" />
                <span>Deterministic Legal Rule & Verification Engine (Recommended)</span>
              </span>
              <span className="text-[10px] bg-blue-600/10 text-blue-600 font-bold px-2 py-0.5 rounded">
                DEFAULT & TESTED
              </span>
            </div>
            <p className="text-xs text-[var(--text-muted)] leading-relaxed">
              Zero hallucination risk. Uses local BM25 ranking, exact character-offset passage tracking, and
              invariant validators. Requires no GPU, model downloads, or API keys.
            </p>
          </div>

          <div
            onClick={() => setProviderMode('ollama')}
            className={`p-4 rounded-xl border cursor-pointer transition-all space-y-1.5 ${
              providerMode === 'ollama'
                ? 'border-blue-600 bg-blue-50/40 dark:bg-blue-950/20'
                : 'border-[var(--border-color)] bg-[var(--bg-input)]/20'
            }`}
          >
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-[var(--text-primary)] flex items-center gap-2">
                <Cpu className="w-4 h-4 text-purple-600" />
                <span>Local Server / Ollama Interface (Qwen 2.5 / DeepSeek R1)</span>
              </span>
              <span className="text-[10px] bg-[var(--bg-input)] text-[var(--text-muted)] font-semibold px-2 py-0.5 rounded">
                PLUGGABLE
              </span>
            </div>
            <p className="text-xs text-[var(--text-muted)] leading-relaxed">
              Connects to a locally running inference server (e.g. `http://localhost:11434`). Passages must still pass
              citation invariant validation before rendering.
            </p>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-blue-50/70 dark:bg-blue-950/20 border border-blue-200/60 dark:border-blue-900/60 text-xs flex items-center gap-2 text-blue-900 dark:text-blue-300">
          <Info className="w-4 h-4 shrink-0 text-blue-600" />
          <span>
            <strong>Audit Transparency Note:</strong> All sample scenarios and evaluation benchmarks execute under the deterministic verification engine for 100% reproducible test assertions.
          </span>
        </div>
      </div>

      {/* Workspace Persistence Details */}
      <div className="p-6 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-xs space-y-4">
        <h3 className="font-bold text-sm text-[var(--text-primary)] flex items-center gap-2">
          <Database className="w-4 h-4 text-blue-600" />
          <span>SQLite Database & Storage Engine</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-[var(--bg-input)]/40 border border-[var(--border-color)] space-y-1">
            <span className="text-[var(--text-muted)] font-medium">Database Backend</span>
            <p className="font-bold text-[var(--text-primary)]">SQLite 3 (Local-First WAL Mode)</p>
          </div>
          <div className="p-3 rounded-xl bg-[var(--bg-input)]/40 border border-[var(--border-color)] space-y-1">
            <span className="text-[var(--text-muted)] font-medium">File Storage Directory</span>
            <p className="font-mono text-[11px] text-[var(--text-primary)]">storage/caselens_documents/</p>
          </div>
          <div className="p-3 rounded-xl bg-[var(--bg-input)]/40 border border-[var(--border-color)] space-y-1">
            <span className="text-[var(--text-muted)] font-medium">Active Workspace ID</span>
            <p className="font-mono text-[11px] text-blue-600">{ws?.id}</p>
          </div>
          <div className="p-3 rounded-xl bg-[var(--bg-input)]/40 border border-[var(--border-color)] space-y-1">
            <span className="text-[var(--text-muted)] font-medium">FastAPI Backend Status</span>
            <p className="font-bold text-emerald-600">
              {healthStatus?.status === 'online' ? 'Connected & Healthy (Port 8000)' : 'Checking...'}
            </p>
          </div>
        </div>
      </div>

      {/* Demo Workspace Reset Action */}
      <div className="p-6 rounded-2xl border border-amber-300/60 dark:border-amber-800/60 bg-amber-50/30 dark:bg-amber-950/15 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-bold text-sm text-amber-900 dark:text-amber-200">
              Reset Sample Demonstration Case
            </h3>
            <p className="text-xs text-amber-800 dark:text-amber-300/80 mt-0.5">
              Restores Project Meridian agreements, seeds deterministic Q&A runs, and clears temporary uploads.
            </p>
          </div>
          <button
            onClick={handleResetDemo}
            disabled={resetting}
            className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold shadow-xs flex items-center gap-2 transition-all disabled:opacity-50 shrink-0"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${resetting ? 'animate-spin' : ''}`} />
            <span>{resetting ? 'Resetting...' : 'Reset Demo Workspace'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
