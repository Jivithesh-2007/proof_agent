"""CaseLens AI data models and schemas."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# ==================== Workspace Models ====================
class WorkspaceBase(BaseModel):
    name: str
    description: Optional[str] = None

class WorkspaceCreate(WorkspaceBase):
    pass

class Workspace(WorkspaceBase):
    id: str
    created_at: str
    is_demo: bool = False
    document_count: int = 0
    analysis_count: int = 0


# ==================== Document Models ====================
class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    char_start: int = 0
    char_end: int = 0
    text: str
    section_heading: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentMetadata(BaseModel):
    document_id: str
    workspace_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    content_hash: str
    page_count: int
    chunk_count: int
    created_at: str
    processing_status: str = "processed"  # "processing", "processed", "failed"
    error_message: Optional[str] = None
    is_demo: bool = False


# ==================== Citation & Evidence Models ====================
class Citation(BaseModel):
    citation_id: str
    document_id: str
    document_name: str
    page_number: int
    section: Optional[str] = None
    quoted_text: str
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    confidence_score: float = 1.0
    verification_status: str = "supported"  # "supported", "partially_supported", "unsupported", "needs_human_review"
    validation_note: Optional[str] = None

class EvidenceVerification(BaseModel):
    is_valid: bool
    citation_id_valid: bool
    document_exists: bool
    passage_match_verified: bool
    claim_supported: bool
    verification_status: str  # "supported by source", "partially supported", "unsupported", "needs human review"
    processing_mode: str = "deterministic_engine"  # "real_model" or "deterministic_engine"
    limitations: List[str] = Field(default_factory=list)


# ==================== Q&A Models ====================
class QuestionRequest(BaseModel):
    workspace_id: str
    question: str
    document_ids: Optional[List[str]] = None
    strict_evidence_only: bool = True

class ClaimEvidence(BaseModel):
    claim_text: str
    supporting_citations: List[Citation] = Field(default_factory=list)
    support_status: str = "supported"  # "supported", "insufficient_evidence", "needs_review"

class QuestionAnswerResponse(BaseModel):
    query_id: str
    question: str
    answer: str
    has_sufficient_evidence: bool
    claims: List[ClaimEvidence] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    searched_document_ids: List[str] = Field(default_factory=list)
    verification: EvidenceVerification
    created_at: str


# ==================== Case Analysis Models ====================
class EntityRecord(BaseModel):
    name: str
    category: str  # "Organization", "Person", "Date", "Monetary", "Jurisdiction", "Clause"
    mention_count: int
    source_documents: List[str] = Field(default_factory=list)
    sample_context: str

class ObligationItem(BaseModel):
    obligation_id: str
    responsible_party: str
    obligation_text: str
    deadline_or_frequency: Optional[str] = None
    source_document: str
    page_number: int
    citation: Optional[Citation] = None
    status: str = "active"

class TimelineEvent(BaseModel):
    event_id: str
    date_str: str
    normalized_date: Optional[str] = None
    description: str
    source_document: str
    page_number: int
    citation: Optional[Citation] = None

class RiskObservation(BaseModel):
    risk_id: str
    severity: str  # "high", "medium", "low", "advisory"
    category: str  # "Contradiction", "Missing Clause", "Termination Risk", "Indemnity Exposure", "Ambiguity"
    title: str
    description: str
    source_document: Optional[str] = None
    recommendation: str

class EvidenceRegisterItem(BaseModel):
    finding_id: str
    claim_or_observation: str
    source_document: str
    page_number: int
    evidence_passage: str
    confidence_or_status: str  # "High Confidence", "Medium Confidence", "Needs Review"
    verification_result: str  # "VERIFIED_SOURCE_GROUNDED", "PARTIALLY_VERIFIED", "UNVERIFIED"

class CaseAnalysisResponse(BaseModel):
    analysis_id: str
    workspace_id: str
    case_title: str
    executive_summary: str
    document_count: int
    parties_and_entities: List[EntityRecord] = Field(default_factory=list)
    obligations: List[ObligationItem] = Field(default_factory=list)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    risks_and_observations: List[RiskObservation] = Field(default_factory=list)
    evidence_register: List[EvidenceRegisterItem] = Field(default_factory=list)
    created_at: str


# ==================== Contradiction Detection Models ====================
class ContradictionItem(BaseModel):
    contradiction_id: str
    category: str  # "Date Mismatch", "Payment Term Conflict", "Notice Period Conflict", "Jurisdiction Dispute"
    summary: str
    doc_a_name: str
    doc_a_page: int
    doc_a_passage: str
    doc_b_name: str
    doc_b_page: int
    doc_b_passage: str
    status: str = "Potential Contradiction"
    review_recommendation: str
    severity: str = "high"

class ContradictionResponse(BaseModel):
    workspace_id: str
    total_contradictions: int
    findings: List[ContradictionItem] = Field(default_factory=list)
    evaluated_document_ids: List[str] = Field(default_factory=list)
    analysis_mode: str = "deterministic_rule_engine"


# ==================== Document Comparison Models ====================
class ClauseComparisonItem(BaseModel):
    section_title: str
    change_type: str  # "identical", "modified", "added_in_b", "removed_in_b"
    doc_a_text: Optional[str] = None
    doc_b_text: Optional[str] = None
    observation: str

class DocumentComparisonResponse(BaseModel):
    doc_a_id: str
    doc_a_name: str
    doc_b_id: str
    doc_b_name: str
    similarity_score: float
    added_clauses: int
    removed_clauses: int
    modified_clauses: int
    clause_comparisons: List[ClauseComparisonItem] = Field(default_factory=list)
    key_differences: List[str] = Field(default_factory=list)


# ==================== Missing Information Models ====================
class MissingFieldCheck(BaseModel):
    field_name: str
    category: str
    expected_importance: str  # "critical", "standard", "optional"
    status: str  # "present", "missing", "ambiguous", "requires_manual_confirmation"
    found_evidence: Optional[str] = None
    review_note: str

class MissingInfoAnalysisResponse(BaseModel):
    workspace_id: str
    template_type: str  # "service_agreement", "employment_agreement", "commercial_lease", "general_contract"
    present_count: int
    missing_count: int
    ambiguous_count: int
    checks: List[MissingFieldCheck] = Field(default_factory=list)
    disclaimer: str = "Missing information reflects a template comparison observation and does not constitute formal legal invalidity."


# ==================== Report Models ====================
class ReportExportResponse(BaseModel):
    report_id: str
    workspace_id: str
    title: str
    executive_summary: str
    documents_analyzed: List[str]
    findings_count: int
    contradictions_count: int
    markdown_content: str
    created_at: str
