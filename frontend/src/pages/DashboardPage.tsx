import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Analysis, Dataset } from '../types';
import { getAnalyses } from '../services/analysis';
import { getDatasets } from '../services/datasets';
import { StatCard } from '../components/dashboard/StatCard';
import { RecentAnalyses } from '../components/dashboard/RecentAnalyses';
import { QuickStart } from '../components/dashboard/QuickStart';
import { Button } from '../components/common/Button';
import { CheckCircle2, ShieldCheck, Database, Activity, Plus, UploadCloud } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);

  useEffect(() => {
    getAnalyses().then(setAnalyses);
    getDatasets().then(setDatasets);
  }, []);

  const totalRows = datasets.reduce((sum, d) => sum + d.rows, 0);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b theme-border pb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight">
            ProofAI Control Plane
          </h1>
          <p className="text-sm theme-text-muted mt-1">
            Deterministic, proof-carrying data analysis with zero external LLM dependencies.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={() => navigate('/data')}>
            <UploadCloud className="w-4 h-4" /> Upload Dataset
          </Button>
          <Button variant="primary" onClick={() => navigate('/analysis')}>
            <Plus className="w-4 h-4" /> New Analysis
          </Button>
        </div>
      </div>

      {/* Dynamic KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Registered Datasets"
          value={String(datasets.length)}
          subtext="Cryptographically fingerprinted"
          icon={Database}
          accentColor="red"
        />
        <StatCard
          label="Total Records"
          value={totalRows.toLocaleString()}
          subtext="Available for query execution"
          icon={Activity}
          accentColor="slate"
        />
        <StatCard
          label="Rule Analyst Engine"
          value="Ready"
          subtext="IF-THEN Analytical Reasoning"
          icon={ShieldCheck}
          trend="Deterministic"
          accentColor="red"
        />
        <StatCard
          label="Verification Policy"
          value="Strict"
          subtext="Independent Reference Engine"
          icon={CheckCircle2}
          trend="100% Invariant Check"
          accentColor="red"
        />
      </div>

      {/* Quick Start Cards */}
      <QuickStart />

      {/* Recent Analysis Table */}
      {analyses.length > 0 && <RecentAnalyses analyses={analyses.slice(0, 5)} />}
    </div>
  );
};
