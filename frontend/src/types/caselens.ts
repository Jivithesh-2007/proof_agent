export interface Workspace {
  id: string;
  name: string;
  description?: string;
  is_demo: boolean;
  created_at: string;
  document_count: number;
  analysis_count: number;
}

export interface DocumentMetadata {
  document_id: string;
  workspace_id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  content_hash: string;
  page_count: number;
  chunk_count: number;
  created_at: string;
  processing_status: 'processing' | 'processed' | 'failed';
  error_message?: string;
  is_demo: boolean;
}

export interface DocumentChunk {
  chunk_id: string;
  document_id: string;
  document_name: string;
  page_number: number;
  char_start: number;
  char_end: number;
  text: string;
  section_heading?: string;
  metadata?: Record<string, any>;
}

export interface Citation {
  citation_id: string;
  document_id: string;
  document_name: string;
  page_number: number;
  section?: string;
  quoted_text: string;
  char_start?: number;
  char_end?: number;
  confidence_score: number;
  verification_status: 'supported' | 'partially_supported' | 'unsupported' | 'needs_human_review';
  validation_note?: string;
}

export interface EvidenceVerification {
  is_valid: boolean;
  citation_id_valid: boolean;
  document_exists: boolean;
  passage_match_verified: boolean;
  claim_supported: boolean;
  verification_status: string;
  processing_mode: string;
  limitations: string[];
}

export interface ClaimEvidence {
  claim_text: string;
  supporting_citations: Citation[];
  support_status: string;
}

export interface QuestionAnswerResponse {
  query_id: string;
  question: string;
  answer: string;
  has_sufficient_evidence: boolean;
  claims: ClaimEvidence[];
  citations: Citation[];
  searched_document_ids: string[];
  verification: EvidenceVerification;
  created_at: string;
}

export interface EntityRecord {
  name: string;
  category: string;
  mention_count: number;
  source_documents: string[];
  sample_context: string;
}

export interface ObligationItem {
  obligation_id: string;
  responsible_party: string;
  obligation_text: string;
  deadline_or_frequency?: string;
  source_document: string;
  page_number: number;
  citation?: Citation;
  status: string;
}

export interface TimelineEvent {
  event_id: string;
  date_str: string;
  normalized_date?: string;
  description: string;
  source_document: string;
  page_number: number;
  citation?: Citation;
}

export interface RiskObservation {
  risk_id: string;
  severity: 'high' | 'medium' | 'low' | 'advisory';
  category: string;
  title: string;
  description: string;
  source_document?: string;
  recommendation: string;
}

export interface EvidenceRegisterItem {
  finding_id: string;
  claim_or_observation: string;
  source_document: string;
  page_number: number;
  evidence_passage: string;
  confidence_or_status: string;
  verification_result: string;
}

export interface CaseAnalysisResponse {
  analysis_id: string;
  workspace_id: string;
  case_title: string;
  executive_summary: string;
  document_count: number;
  parties_and_entities: EntityRecord[];
  obligations: ObligationItem[];
  timeline: TimelineEvent[];
  risks_and_observations: RiskObservation[];
  evidence_register: EvidenceRegisterItem[];
  created_at: string;
}

export interface ContradictionItem {
  contradiction_id: string;
  category: string;
  summary: string;
  doc_a_name: string;
  doc_a_page: number;
  doc_a_passage: string;
  doc_b_name: string;
  doc_b_page: number;
  doc_b_passage: string;
  status: string;
  review_recommendation: string;
  severity: string;
}

export interface ContradictionResponse {
  workspace_id: string;
  total_contradictions: number;
  findings: ContradictionItem[];
  evaluated_document_ids: string[];
  analysis_mode: string;
}

export interface ClauseComparisonItem {
  section_title: string;
  change_type: 'identical' | 'modified' | 'added_in_b' | 'removed_in_b';
  doc_a_text?: string;
  doc_b_text?: string;
  observation: string;
}

export interface DocumentComparisonResponse {
  doc_a_id: string;
  doc_a_name: string;
  doc_b_id: string;
  doc_b_name: string;
  similarity_score: number;
  added_clauses: number;
  removed_clauses: number;
  modified_clauses: number;
  clause_comparisons: ClauseComparisonItem[];
  key_differences: string[];
}

export interface MissingFieldCheck {
  field_name: string;
  category: string;
  expected_importance: string;
  status: 'present' | 'missing' | 'ambiguous' | 'requires_manual_confirmation';
  found_evidence?: string;
  review_note: string;
}

export interface MissingInfoAnalysisResponse {
  workspace_id: string;
  template_type: string;
  present_count: number;
  missing_count: number;
  ambiguous_count: number;
  checks: MissingFieldCheck[];
  disclaimer: string;
}

export interface ReportExportResponse {
  report_id: string;
  workspace_id: string;
  title: string;
  executive_summary: string;
  documents_analyzed: string[];
  findings_count: number;
  contradictions_count: number;
  markdown_content: string;
  created_at: string;
}
