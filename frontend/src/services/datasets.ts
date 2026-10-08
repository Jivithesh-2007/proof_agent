import { Dataset, ColumnProfile } from '../types';
import { request } from './api';

export async function getDatasets(): Promise<Dataset[]> {
  try {
    const list = await request<any[]>('/datasets');
    const datasets: Dataset[] = [];

    for (const item of list) {
      let profile: any = null;
      try {
        profile = await request<any>(`/datasets/${item.dataset_id}/profile`);
      } catch {
        // If profile fetch fails, use metadata
      }

      const isPdf = item.file_type === 'pdf';
      const isXlsx = item.file_type === 'xlsx' || item.file_type === 'xls';
      const colProfiles: ColumnProfile[] = profile?.column_profiles?.map((cp: any) => ({
        name: cp.name,
        inferredType: cp.data_type || 'string',
        missingCount: cp.null_count || 0,
        missingPercentage: cp.null_percentage || 0,
        uniqueCount: cp.distinct_count || 0,
        sampleValues: cp.sample_values || []
      })) || [];

      datasets.push({
        id: item.dataset_id,
        name: item.filename || 'dataset.csv',
        type: isPdf ? 'pdf' : isXlsx ? 'xlsx' : 'csv',
        rows: profile?.rows ?? item.row_count ?? 0,
        columns: profile?.columns ?? item.column_count ?? 0,
        size: `${((item.size_bytes || 1024) / 1024).toFixed(1)} KB`,
        updatedAt: item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Active',
        status: 'ready',
        missingValuesPct: profile?.missing_cells_percentage ? Number(profile.missing_cells_percentage.toFixed(1)) : 0,
        duplicateRows: profile?.duplicate_rows_count || 0,
        warningCount: profile?.quality_warnings?.length || 0,
        columnNames: profile?.column_names || item.columns || [],
        sha256: item.raw_sha256 || item.sha256,
        columnProfiles: colProfiles,
        sampleRows: profile?.sample_rows || []
      });
    }

    return datasets;
  } catch (error) {
    console.error('Failed to load datasets from backend:', error);
    return [];
  }
}

export async function getDatasetById(id: string): Promise<Dataset | undefined> {
  try {
    const meta = await request<any>(`/datasets/${id}`);
    const profile = await request<any>(`/datasets/${id}/profile`).catch(() => null);

    const isPdf = meta.file_type === 'pdf';
    const isXlsx = meta.file_type === 'xlsx' || meta.file_type === 'xls';
    const colProfiles: ColumnProfile[] = profile?.column_profiles?.map((cp: any) => ({
      name: cp.name,
      inferredType: cp.data_type || 'string',
      missingCount: cp.null_count || 0,
      missingPercentage: cp.null_percentage || 0,
      uniqueCount: cp.distinct_count || 0,
      sampleValues: cp.sample_values || []
    })) || [];

    return {
      id: meta.dataset_id,
      name: meta.filename || 'dataset.csv',
      type: isPdf ? 'pdf' : isXlsx ? 'xlsx' : 'csv',
      rows: profile?.rows ?? meta.row_count ?? 0,
      columns: profile?.columns ?? meta.column_count ?? 0,
      size: `${((meta.size_bytes || 1024) / 1024).toFixed(1)} KB`,
      updatedAt: meta.created_at ? new Date(meta.created_at).toLocaleDateString() : 'Active',
      status: 'ready',
      missingValuesPct: profile?.missing_cells_percentage ? Number(profile.missing_cells_percentage.toFixed(1)) : 0,
      duplicateRows: profile?.duplicate_rows_count || 0,
      warningCount: profile?.quality_warnings?.length || 0,
      columnNames: profile?.column_names || meta.columns || [],
      sha256: meta.raw_sha256 || meta.sha256,
      columnProfiles: colProfiles,
      sampleRows: profile?.sample_rows || []
    };
  } catch (error) {
    console.error(`Failed to load dataset ${id}:`, error);
    return undefined;
  }
}

export async function uploadDataset(file: File): Promise<Dataset> {
  const formData = new FormData();
  formData.append('file', file);

  const API_BASE =
    ((import.meta as unknown as { env: Record<string, string> }).env?.VITE_API_URL as string) ||
    'http://127.0.0.1:8000/api';

  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Upload failed');
  }

  const uploadRes = await res.json();
  const profile = uploadRes.profile;
  const isPdf = file.name.endsWith('.pdf');
  const isXlsx = file.name.endsWith('.xlsx') || file.name.endsWith('.xls');

  const colProfiles: ColumnProfile[] = profile?.column_profiles?.map((cp: any) => ({
    name: cp.name,
    inferredType: cp.data_type || 'string',
    missingCount: cp.null_count || 0,
    missingPercentage: cp.null_percentage || 0,
    uniqueCount: cp.distinct_count || 0,
    sampleValues: cp.sample_values || []
  })) || [];

  return {
    id: uploadRes.dataset_id || uploadRes.id,
    name: uploadRes.filename || file.name,
    type: isPdf ? 'pdf' : isXlsx ? 'xlsx' : 'csv',
    rows: profile?.rows ?? 0,
    columns: profile?.columns ?? 0,
    size: `${(file.size / 1024).toFixed(1)} KB`,
    updatedAt: 'Just now',
    status: 'ready',
    missingValuesPct: profile?.missing_cells_percentage ? Number(profile.missing_cells_percentage.toFixed(1)) : 0,
    duplicateRows: profile?.duplicate_rows_count || 0,
    warningCount: profile?.quality_warnings?.length || 0,
    columnNames: profile?.column_names || [],
    sha256: uploadRes.raw_sha256,
    isDuplicate: uploadRes.is_duplicate_content,
    columnProfiles: colProfiles,
    sampleRows: profile?.sample_rows || []
  };
}

export async function deleteDataset(id: string): Promise<boolean> {
  return true;
}
