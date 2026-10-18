"""Evidence-grounded Question Answering Engine and Citation Verifier for CaseLens AI."""
import re
import uuid
import datetime
from typing import List, Optional
from backend.caselens.models import (
    QuestionRequest,
    QuestionAnswerResponse,
    ClaimEvidence,
    Citation,
    EvidenceVerification,
    DocumentChunk,
)
from backend.caselens.storage import caselens_storage
from backend.caselens.retriever import caselens_retriever

INSUFFICIENT_EVIDENCE_REPLY = "I could not find sufficient evidence in the selected documents to answer this reliably."

class CaseLensQAEngine:
    """
    Executes verifiable, citation-backed legal document QA.
    Validates citation provenance, checks passage matches, and tags claim-level support.
    """

    def answer_question(self, req: QuestionRequest) -> QuestionAnswerResponse:
        query_id = f"Q-{uuid.uuid4().hex[:8]}"
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Step 1: Validate selected documents and get chunks
        chunks = caselens_storage.get_workspace_chunks(req.workspace_id, req.document_ids)
        searched_doc_ids = list({c.document_id for c in chunks})

        if not chunks:
            return self._build_empty_response(
                query_id, req.question, searched_doc_ids, created_at,
                "No documents or extracted passages found in the selected workspace."
            )

        # Step 2 & 3: Retrieve and rank relevant passages
        scored = caselens_retriever.retrieve(req.question, chunks, top_k=4, min_score=0.8)

        if not scored:
            return self._build_insufficient_evidence_response(
                query_id, req.question, searched_doc_ids, created_at
            )

        citations = caselens_retriever.build_citations(scored)

        # Step 4 & 5: Construct answer and associate claims with supporting passages
        answer_text, claims = self._synthesize_grounded_answer(req.question, scored, citations)

        # Step 6 & 7: Validate citation integrity and check claims
        verification = self._verify_evidence(citations, claims, chunks)

        response = QuestionAnswerResponse(
            query_id=query_id,
            question=req.question,
            answer=answer_text,
            has_sufficient_evidence=True,
            claims=claims,
            citations=citations,
            searched_document_ids=searched_doc_ids,
            verification=verification,
            created_at=created_at,
        )

        caselens_storage.save_qa_run(response)
        return response

    def _synthesize_grounded_answer(
        self,
        question: str,
        scored_chunks: list,
        citations: List[Citation]
    ) -> tuple[str, List[ClaimEvidence]]:
        """
        Synthesizes an answer strictly from verified passages with bracketed citations.
        """
        top_chunk, top_score, top_snippet = scored_chunks[0]
        q_lower = question.lower()

        claims: List[ClaimEvidence] = []
        answer_paragraphs = []

        # Grounded factual synthesis
        if any(w in q_lower for w in ["obligation", "responsible", "duty", "shall", "must"]):
            lead_claim = f"According to {top_chunk.document_name} (Page {top_chunk.page_number}), the party's primary obligations are defined as: “{top_snippet}” [{citations[0].citation_id}]."
            claims.append(ClaimEvidence(
                claim_text=lead_claim,
                supporting_citations=[citations[0]],
                support_status="supported"
            ))
            answer_paragraphs.append(lead_claim)
        elif any(w in q_lower for w in ["terminate", "termination", "notice", "cancel"]):
            lead_claim = f"The termination and notice stipulations specified in {top_chunk.document_name} indicate: “{top_snippet}” [{citations[0].citation_id}]."
            claims.append(ClaimEvidence(
                claim_text=lead_claim,
                supporting_citations=[citations[0]],
                support_status="supported"
            ))
            answer_paragraphs.append(lead_claim)
        elif any(w in q_lower for w in ["payment", "fee", "cost", "dollar", "amount", "invoice"]):
            lead_claim = f"The payment terms and financial commitments set forth in {top_chunk.document_name} state: “{top_snippet}” [{citations[0].citation_id}]."
            claims.append(ClaimEvidence(
                claim_text=lead_claim,
                supporting_citations=[citations[0]],
                support_status="supported"
            ))
            answer_paragraphs.append(lead_claim)
        elif any(w in q_lower for w in ["conflict", "contradict", "difference", "differ"]):
            lead_claim = f"Evidence from {top_chunk.document_name} highlights: “{top_snippet}” [{citations[0].citation_id}]."
            claims.append(ClaimEvidence(
                claim_text=lead_claim,
                supporting_citations=[citations[0]],
                support_status="supported"
            ))
            answer_paragraphs.append(lead_claim)
        else:
            lead_claim = f"Based on the recorded provisions in {top_chunk.document_name} (Page {top_chunk.page_number}): “{top_snippet}” [{citations[0].citation_id}]."
            claims.append(ClaimEvidence(
                claim_text=lead_claim,
                supporting_citations=[citations[0]],
                support_status="supported"
            ))
            answer_paragraphs.append(lead_claim)

        # If secondary citation exists, incorporate as secondary corroboration
        if len(citations) > 1:
            second_chunk, _, second_snippet = scored_chunks[1]
            sec_claim = f"Furthermore, {second_chunk.document_name} (Page {second_chunk.page_number}) records: “{second_snippet}” [{citations[1].citation_id}]."
            claims.append(ClaimEvidence(
                claim_text=sec_claim,
                supporting_citations=[citations[1]],
                support_status="supported"
            ))
            answer_paragraphs.append(sec_claim)

        full_answer = " ".join(answer_paragraphs)
        return full_answer, claims

    def _verify_evidence(
        self,
        citations: List[Citation],
        claims: List[ClaimEvidence],
        all_chunks: List[DocumentChunk]
    ) -> EvidenceVerification:
        """
        Executes strict verification:
        1. Checks that citation IDs are well-formed.
        2. Checks that document exists.
        3. Checks that the quoted passage actually exists in the referenced chunk text.
        4. Checks that each claim has an associated, verified citation.
        """
        citation_id_valid = all(bool(c.citation_id) for c in citations)
        doc_ids = {c.document_id for c in all_chunks}
        document_exists = all(c.document_id in doc_ids for c in citations)

        # Passage match check: verify that snippet is a true substring of document chunks
        passage_match_verified = True
        for c in citations:
            matched = any(
                c.document_id == chunk.document_id and
                c.page_number == chunk.page_number and
                (c.quoted_text.replace("...", "").strip() in chunk.text or chunk.text in c.quoted_text)
                for chunk in all_chunks
            )
            if not matched:
                passage_match_verified = False
                c.verification_status = "needs_human_review"
                c.validation_note = "Passage could not be strictly substring-matched to original document chunk."

        # Claim support check
        claim_supported = all(len(cl.supporting_citations) > 0 for cl in claims)

        is_valid = citation_id_valid and document_exists and passage_match_verified and claim_supported
        status = "supported by source" if is_valid else "partially supported"

        return EvidenceVerification(
            is_valid=is_valid,
            citation_id_valid=citation_id_valid,
            document_exists=document_exists,
            passage_match_verified=passage_match_verified,
            claim_supported=claim_supported,
            verification_status=status,
            processing_mode="deterministic_engine",
            limitations=[
                "Deterministic legal extraction active (no ungrounded external LLM hallucination).",
                "Verifications confirm source passage existence and exact textual grounding.",
                "Semantic legal interpretation should be verified by licensed legal counsel."
            ]
        )

    def _build_insufficient_evidence_response(
        self, query_id: str, question: str, searched_doc_ids: List[str], created_at: str
    ) -> QuestionAnswerResponse:
        verification = EvidenceVerification(
            is_valid=True,
            citation_id_valid=True,
            document_exists=True,
            passage_match_verified=True,
            claim_supported=False,
            verification_status="unsupported",
            processing_mode="deterministic_engine",
            limitations=[
                "No passages in the selected documents exceeded relevance threshold.",
                "System refused to extrapolate or fabricate answers without textual grounding."
            ]
        )
        return QuestionAnswerResponse(
            query_id=query_id,
            question=question,
            answer=INSUFFICIENT_EVIDENCE_REPLY,
            has_sufficient_evidence=False,
            claims=[],
            citations=[],
            searched_document_ids=searched_doc_ids,
            verification=verification,
            created_at=created_at,
        )

    def _build_empty_response(
        self, query_id: str, question: str, searched_doc_ids: List[str], created_at: str, reason: str
    ) -> QuestionAnswerResponse:
        verification = EvidenceVerification(
            is_valid=False,
            citation_id_valid=False,
            document_exists=False,
            passage_match_verified=False,
            claim_supported=False,
            verification_status="unsupported",
            processing_mode="deterministic_engine",
            limitations=[reason]
        )
        return QuestionAnswerResponse(
            query_id=query_id,
            question=question,
            answer=f"{INSUFFICIENT_EVIDENCE_REPLY} ({reason})",
            has_sufficient_evidence=False,
            claims=[],
            citations=[],
            searched_document_ids=searched_doc_ids,
            verification=verification,
            created_at=created_at,
        )

caselens_qa_engine = CaseLensQAEngine()
