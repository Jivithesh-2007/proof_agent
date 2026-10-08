import React, { useEffect, useState } from 'react';
import { Dataset } from '../types';
import { getDatasets, uploadDataset } from '../services/datasets';
import { UploadDropzone } from '../components/data/UploadDropzone';
import { DatasetHeader } from '../components/data/DatasetHeader';
import { DatasetProfile } from '../components/data/DatasetProfile';
import { Modal } from '../components/common/Modal';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { Plus, Database, Table, Fingerprint, ShieldCheck, AlertTriangle, Layers, Copy, CheckCircle2 } from 'lucide-react';

export const DataSourcesPage: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDatasets().then((data) => {
      setDatasets(data);
      if (data.length > 0) setSelectedDataset(data[0]);
      setLoading(false);
    });
  }, []);

  const handleUploadSuccess = (newDs: Dataset) => {
    setDatasets((prev) => {
      const exists = prev.find((d) => d.id === newDs.id);
      if (exists) {
        return prev.map((d) => (d.id === newDs.id ? newDs : d));
      }
      return [newDs, ...prev];
    });
    setSelectedDataset(newDs);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b theme-border pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Data Sources</h1>
          <p className="text-sm theme-text-muted mt-1">
            Upload and inspect verified datasets. SHA-256 fingerprinting ensures cryptographic identity and duplicate detection.
          </p>
        </div>

        <Button variant="primary" onClick={() => window.scrollTo({ top: 180, behavior: 'smooth' })}>
          <Plus className="w-4 h-4" /> Upload Dataset
        </Button>
      </div>

      {/* Upload Dropzone */}
      <div className="space-y-2">
        <h3 className="text-xs font-semibold theme-text-muted uppercase tracking-wider">
          Upload New Dataset
        </h3>
        <UploadDropzone onUploaded={handleUploadSuccess} />
      </div>

      {/* Datasets Selection List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold theme-text-muted uppercase tracking-wider">
            Available Datasets ({datasets.length})
          </h3>
          <span className="text-xs font-mono text-[#E64A32]">Real Backend Storage</span>
        </div>

        {datasets.length === 0 ? (
          <Card className="p-8 text-center theme-text-muted font-mono text-sm">
            No datasets uploaded yet. Upload a CSV or Excel file above to begin.
          </Card>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {datasets.map((ds) => (
              <div
                key={ds.id}
                onClick={() => setSelectedDataset(ds)}
                className={`p-4 rounded-xl border transition-all cursor-pointer flex items-center gap-3 ${
                  selectedDataset?.id === ds.id
                    ? 'bg-[#E64A32]/15 border-[#E64A32] shadow-sm ring-1 ring-[#E64A32]/30'
                    : 'theme-card hover:border-[#E64A32]/50'
                }`}
              >
                <div className="w-10 h-10 rounded-lg theme-input flex items-center justify-center text-[#E64A32] font-mono text-xs border theme-border shrink-0">
                  <Database className="w-5 h-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-semibold truncate font-mono">{ds.name}</h4>
                    {ds.isDuplicate && (
                      <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-[#E18230]/20 text-[#E18230] border border-[#E18230]/40">
                        Duplicate
                      </span>
                    )}
                  </div>
                  <p className="text-xs theme-text-muted font-mono mt-0.5">
                    {ds.size} · {ds.rows.toLocaleString()} rows
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Selected Dataset Inspection */}
      {selectedDataset && (
        <div className="space-y-6 pt-4 border-t theme-border">
          <DatasetHeader
            dataset={selectedDataset}
            onPreview={() => setPreviewOpen(true)}
          />

          <DatasetProfile dataset={selectedDataset} />

          {/* Cryptographic Identity & Metadata Card */}
          <Card className="p-6 space-y-4">
            <div className="flex items-center justify-between border-b theme-border pb-3">
              <h3 className="text-sm font-bold flex items-center gap-2">
                <Fingerprint className="w-4 h-4 text-[#E64A32]" /> SHA-256 Dataset Identity & Integrity
              </h3>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-[#E64A32]/15 text-[#E64A32] border border-[#E64A32]/30">
                Authoritative Fingerprint
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
              <div className="theme-input p-3 rounded-lg border theme-border space-y-1">
                <div className="text-[11px] theme-text-muted font-sans uppercase">Dataset ID</div>
                <div className="text-[#F4F5EC] font-bold">{selectedDataset.id}</div>
              </div>

              <div className="theme-input p-3 rounded-lg border theme-border space-y-1">
                <div className="text-[11px] theme-text-muted font-sans uppercase">SHA-256 Hash</div>
                <div className="text-[#E18230] font-bold truncate" title={selectedDataset.sha256}>
                  {selectedDataset.sha256 || 'SHA-256 computed on ingestion'}
                </div>
              </div>
            </div>
          </Card>

          {/* Schema & Column Profiles Panel */}
          <Card className="p-6 space-y-4">
            <div className="flex items-center justify-between border-b theme-border pb-3">
              <h3 className="text-sm font-bold flex items-center gap-2">
                <Table className="w-4 h-4 text-[#E64A32]" /> Actual Schema & Column Inferences ({selectedDataset.columnNames.length} Columns)
              </h3>
              <span className="text-xs font-mono text-[#F4F5EC]/60">Dynamic Profiler</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 font-mono text-xs">
              {selectedDataset.columnProfiles && selectedDataset.columnProfiles.length > 0 ? (
                selectedDataset.columnProfiles.map((col, idx) => (
                  <div key={idx} className="theme-input p-3 rounded-lg border theme-border space-y-1.5">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-[#F4F5EC] truncate">{col.name}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] bg-[#E64A32]/20 text-[#E64A32] border border-[#E64A32]/30">
                        {col.inferredType}
                      </span>
                    </div>
                    <div className="text-[11px] theme-text-muted flex justify-between">
                      <span>Unique: {col.uniqueCount}</span>
                      <span>Nulls: {col.missingPercentage}%</span>
                    </div>
                  </div>
                ))
              ) : (
                selectedDataset.columnNames.map((name, idx) => (
                  <div key={idx} className="theme-input p-3 rounded-lg border theme-border flex items-center justify-between">
                    <span className="font-bold text-[#F4F5EC]">{name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-[#3C3B39] text-[#F4F5EC]/70">column</span>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Data Preview Modal */}
      {selectedDataset && (
        <Modal
          isOpen={previewOpen}
          onClose={() => setPreviewOpen(false)}
          title={`Preview: ${selectedDataset.name}`}
          subtitle={`${selectedDataset.rows.toLocaleString()} rows · ${selectedDataset.columns} columns · ID: ${selectedDataset.id}`}
          maxWidth="2xl"
        >
          <div className="space-y-4 font-mono text-xs">
            <div className="flex items-center gap-2 theme-text-muted text-xs font-sans pb-2 border-b theme-border">
              <Table className="w-4 h-4 text-[#E64A32]" />
              <span>Showing sample rows from uploaded dataset</span>
            </div>

            <div className="overflow-x-auto">
              {selectedDataset.sampleRows && selectedDataset.sampleRows.length > 0 ? (
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="theme-input border-b theme-border">
                      {Object.keys(selectedDataset.sampleRows[0]).map((col) => (
                        <th key={col} className="p-2 border-r theme-border font-semibold">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y theme-border theme-card">
                    {selectedDataset.sampleRows.slice(0, 5).map((row, rIdx) => (
                      <tr key={rIdx}>
                        {Object.keys(selectedDataset.sampleRows![0]).map((col, cIdx) => (
                          <td key={cIdx} className="p-2 border-r theme-border">
                            {String(row[col])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="p-6 text-center text-xs theme-text-muted">
                  Columns: {selectedDataset.columnNames.join(', ')}
                </div>
              )}
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
