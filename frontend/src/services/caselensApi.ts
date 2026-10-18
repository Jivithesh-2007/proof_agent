import {
  Workspace,
  DocumentMetadata,
  DocumentChunk,
  QuestionAnswerResponse,
  CaseAnalysisResponse,
  ContradictionResponse,
  DocumentComparisonResponse,
  MissingInfoAnalysisResponse,
  ReportExportResponse,
} from '../types/caselens';

const API_BASE = '/api/caselens';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMsg = `HTTP Error ${res.status}: ${res.statusText}`;
    try {
      const data = await res.json();
      if (data.detail) {
        errorMsg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // Keep original error message
    }
    throw new Error(errorMsg);
  }
  return res.json();
}

export const caselensApi = {
  // Health
  checkHealth: async () => {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse<{ status: string; service: string; tagline: string }>(res);
  },

  // Workspaces
  listWorkspaces: async (): Promise<Workspace[]> => {
    const res = await fetch(`${API_BASE}/workspaces`);
    return handleResponse<Workspace[]>(res);
  },

  createWorkspace: async (name: string, description?: string): Promise<Workspace> => {
    const res = await fetch(`${API_BASE}/workspaces`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description }),
    });
    return handleResponse<Workspace>(res);
  },

  getWorkspace: async (workspaceId: string): Promise<Workspace> => {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}`);
    return handleResponse<Workspace>(res);
  },

  deleteWorkspace: async (workspaceId: string): Promise<{ success: boolean; message: string }> => {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}`, { method: 'DELETE' });
    return handleResponse<{ success: boolean; message: string }>(res);
  },

  loadDemoWorkspace: async (): Promise<Workspace> => {
    const res = await fetch(`${API_BASE}/workspaces/demo/load`, { method: 'POST' });
    return handleResponse<Workspace>(res);
  },

  resetDemoWorkspace: async (): Promise<{ success: boolean; workspace: Workspace }> => {
    const res = await fetch(`${API_BASE}/workspaces/demo/reset`, { method: 'POST' });
    return handleResponse<{ success: boolean; workspace: Workspace }>(res);
  },

  // Documents
  listDocuments: async (workspaceId: string): Promise<DocumentMetadata[]> => {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/documents`);
    return handleResponse<DocumentMetadata[]>(res);
  },

  uploadDocument: async (workspaceId: string, file: File): Promise<DocumentMetadata> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<DocumentMetadata>(res);
  },

  getDocument: async (documentId: string): Promise<DocumentMetadata> => {
    const res = await fetch(`${API_BASE}/documents/${documentId}`);
    return handleResponse<DocumentMetadata>(res);
  },

  getDocumentChunks: async (documentId: string): Promise<DocumentChunk[]> => {
    const res = await fetch(`${API_BASE}/documents/${documentId}/chunks`);
    return handleResponse<DocumentChunk[]>(res);
  },

  getDocumentText: async (documentId: string): Promise<{ document_id: string; text: string }> => {
    const res = await fetch(`${API_BASE}/documents/${documentId}/text`);
    return handleResponse<{ document_id: string; text: string }>(res);
  },

  deleteDocument: async (documentId: string): Promise<{ success: boolean; message: string }> => {
    const res = await fetch(`${API_BASE}/documents/${documentId}`, { method: 'DELETE' });
    return handleResponse<{ success: boolean; message: string }>(res);
  },

  // Search
  searchDocuments: async (workspaceId: string, query: string, topK = 5) => {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/search?q=${encodeURIComponent(query)}&top_k=${topK}`);
    return handleResponse<{ query: string; total_results: number; results: any[] }>(res);
  },

  // Q&A
  askQuestion: async (
    workspaceId: string,
    question: string,
    documentIds?: string[],
    strictEvidenceOnly = true
  ): Promise<QuestionAnswerResponse> => {
    const res = await fetch(`${API_BASE}/qa/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workspace_id: workspaceId,
        question,
        document_ids: documentIds,
        strict_evidence_only: strictEvidenceOnly,
      }),
    });
    return handleResponse<QuestionAnswerResponse>(res);
  },

  getQAHistory: async (workspaceId: string): Promise<QuestionAnswerResponse[]> => {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/qa/history`);
    return handleResponse<QuestionAnswerResponse[]>(res);
  },

  // Case Analysis
  getCaseAnalysis: async (workspaceId: string): Promise<CaseAnalysisResponse> => {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/analysis`);
    return handleResponse<CaseAnalysisResponse>(res);
  },

  triggerCaseAnalysis: async (workspaceId: string): Promise<CaseAnalysisResponse> => {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/analyze`, { method: 'POST' });
    return handleResponse<CaseAnalysisResponse>(res);
  },

  // Contradictions
  getContradictions: async (workspaceId: string): Promise<ContradictionResponse> => {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/contradictions`);
    return handleResponse<ContradictionResponse>(res);
  },

  // Missing Information
  getMissingInfo: async (workspaceId: string, template = 'service_agreement'): Promise<MissingInfoAnalysisResponse> => {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/missing-info?template=${encodeURIComponent(template)}`);
    return handleResponse<MissingInfoAnalysisResponse>(res);
  },

  // Document Comparison
  compareDocuments: async (docA: string, docB: string): Promise<DocumentComparisonResponse> => {
    const res = await fetch(`${API_BASE}/compare?doc_a=${encodeURIComponent(docA)}&doc_b=${encodeURIComponent(docB)}`);
    return handleResponse<DocumentComparisonResponse>(res);
  },

  // Reports
  createReport: async (workspaceId: string, title?: string): Promise<ReportExportResponse> => {
    const formData = new FormData();
    if (title) formData.append('title', title);
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/reports`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<ReportExportResponse>(res);
  },

  listReports: async (workspaceId: string): Promise<ReportExportResponse[]> => {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/reports`);
    return handleResponse<ReportExportResponse[]>(res);
  },

  getReport: async (reportId: string): Promise<ReportExportResponse> => {
    const res = await fetch(`${API_BASE}/reports/${reportId}`);
    return handleResponse<ReportExportResponse>(res);
  },

  downloadReportMarkdownUrl: (reportId: string): string => {
    return `${API_BASE}/reports/${reportId}/download`;
  },
};
