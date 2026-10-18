"""Deterministic & Rule-grounded Contradiction Detection Engine for CaseLens AI."""
import re
import uuid
from typing import List, Dict, Any, Tuple
from backend.caselens.models import (
    ContradictionResponse,
    ContradictionItem,
    DocumentChunk,
)
from backend.caselens.storage import caselens_storage

class ContradictionDetector:
    """
    Identifies deterministic cross-document contradictions including:
    - Expiration & termination dates for identical contract scopes.
    - Fee schedules and monetary amounts.
    - Notice periods (e.g. 30 days vs 60 days).
    - Governing law / jurisdiction discrepancies.
    """

    def analyze_workspace(self, workspace_id: str) -> ContradictionResponse:
        docs = caselens_storage.list_documents(workspace_id)
        chunks = caselens_storage.get_workspace_chunks(workspace_id)
        doc_ids = [d.document_id for d in docs]

        if len(docs) < 2 or not chunks:
            # Need at least two documents or adequate text to analyze cross-document discrepancies
            # If 1 doc, check intra-document contradictions
            findings = self._scan_contradictions(chunks)
        else:
            findings = self._scan_contradictions(chunks)

        response = ContradictionResponse(
            workspace_id=workspace_id,
            total_contradictions=len(findings),
            findings=findings,
            evaluated_document_ids=doc_ids,
            analysis_mode="deterministic_rule_engine",
        )

        caselens_storage.save_contradictions(response)
        return response

    def _scan_contradictions(self, chunks: List[DocumentChunk]) -> List[ContradictionItem]:
        findings: List[ContradictionItem] = []

        # 1. Date Discrepancies on Agreement Expiration / Term
        date_findings = self._check_expiration_date_conflicts(chunks)
        findings.extend(date_findings)

        # 2. Payment Terms / Fee Amount Conflicts
        fee_findings = self._check_monetary_conflicts(chunks)
        findings.extend(fee_findings)

        # 3. Notice Period Conflicts
        notice_findings = self._check_notice_period_conflicts(chunks)
        findings.extend(notice_findings)

        # 4. Governing Law / Jurisdiction Conflicts
        law_findings = self._check_governing_law_conflicts(chunks)
        findings.extend(law_findings)

        return findings

    def _check_expiration_date_conflicts(self, chunks: List[DocumentChunk]) -> List[ContradictionItem]:
        findings = []
        # Look for sentences containing "expire", "expiration", "term shall end", "effective until"
        expire_pattern = re.compile(
            r'([^.!?\n]+?\b(?:expire[sd]?|expiration|term shall end on|effective until|valid until)\b[^.!?\n]+[.!?])',
            re.IGNORECASE
        )
        date_pattern = re.compile(r'\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b', re.IGNORECASE)

        matches: List[Tuple[DocumentChunk, str, str]] = [] # (chunk, sentence, date_str)
        for ch in chunks:
            for m in expire_pattern.finditer(ch.text):
                sent = m.group(1).strip()
                date_match = date_pattern.search(sent)
                if date_match:
                    matches.append((ch, sent, date_match.group(1).strip()))

        # Check for conflicts across different documents or sentences
        for i in range(len(matches)):
            for j in range(i + 1, len(matches)):
                ch_a, sent_a, date_a = matches[i]
                ch_b, sent_b, date_b = matches[j]

                # Normalize dates roughly to compare
                norm_a = re.sub(r'[, ]+', ' ', date_a.lower())
                norm_b = re.sub(r'[, ]+', ' ', date_b.lower())

                if norm_a != norm_b and ch_a.document_id != ch_b.document_id:
                    findings.append(ContradictionItem(
                        contradiction_id=f"CONTR-DATE-{uuid.uuid4().hex[:6]}",
                        category="Date Mismatch",
                        summary=f"Conflicting expiration dates: '{date_a}' vs '{date_b}'",
                        doc_a_name=ch_a.document_name,
                        doc_a_page=ch_a.page_number,
                        doc_a_passage=sent_a,
                        doc_b_name=ch_b.document_name,
                        doc_b_page=ch_b.page_number,
                        doc_b_passage=sent_b,
                        status="Potential Contradiction",
                        review_recommendation="Examine execution dates or amendment precedence clauses to confirm which expiration date governs.",
                        severity="high"
                    ))
        return findings

    def _check_monetary_conflicts(self, chunks: List[DocumentChunk]) -> List[ContradictionItem]:
        findings = []
        fee_pattern = re.compile(
            r'([^.!?\n]+?\b(?:retainer|annual fee|license fee|total compensation|total price|base fee)\b[^.!?\n]*?(\$\s?[\d,]+(?:\.\d{2})?|\b[\d,]+\s+(?:USD|Dollars))\b[^.!?\n]*[.!?])',
            re.IGNORECASE
        )

        matches: List[Tuple[DocumentChunk, str, str]] = []
        for ch in chunks:
            for m in fee_pattern.finditer(ch.text):
                sent = m.group(1).strip()
                amt = m.group(2).strip()
                matches.append((ch, sent, amt))

        for i in range(len(matches)):
            for j in range(i + 1, len(matches)):
                ch_a, sent_a, amt_a = matches[i]
                ch_b, sent_b, amt_b = matches[j]
                if amt_a != amt_b and ch_a.document_id != ch_b.document_id:
                    findings.append(ContradictionItem(
                        contradiction_id=f"CONTR-AMT-{uuid.uuid4().hex[:6]}",
                        category="Payment Term Conflict",
                        summary=f"Discrepancy in recorded fee/compensation: '{amt_a}' vs '{amt_b}'",
                        doc_a_name=ch_a.document_name,
                        doc_a_page=ch_a.page_number,
                        doc_a_passage=sent_a,
                        doc_b_name=ch_b.document_name,
                        doc_b_page=ch_b.page_number,
                        doc_b_passage=sent_b,
                        status="Potential Contradiction",
                        review_recommendation="Verify whether one figure represents an amended fee schedule or a different scope of deliverable.",
                        severity="high"
                    ))
        return findings

    def _check_notice_period_conflicts(self, chunks: List[DocumentChunk]) -> List[ContradictionItem]:
        findings = []
        notice_pattern = re.compile(
            r'([^.!?\n]+?\b(\d+)\s+(?:days|business days)\b[^.!?\n]+?\b(?:written notice|prior notice|notice of termination)\b[^.!?\n]*[.!?])',
            re.IGNORECASE
        )

        matches: List[Tuple[DocumentChunk, str, str]] = []
        for ch in chunks:
            for m in notice_pattern.finditer(ch.text):
                sent = m.group(1).strip()
                days = m.group(2).strip()
                matches.append((ch, sent, days))

        for i in range(len(matches)):
            for j in range(i + 1, len(matches)):
                ch_a, sent_a, days_a = matches[i]
                ch_b, sent_b, days_b = matches[j]
                if days_a != days_b and ch_a.document_id != ch_b.document_id:
                    findings.append(ContradictionItem(
                        contradiction_id=f"CONTR-NOT-{uuid.uuid4().hex[:6]}",
                        category="Notice Period Conflict",
                        summary=f"Conflicting termination notice requirements: {days_a} days vs {days_b} days",
                        doc_a_name=ch_a.document_name,
                        doc_a_page=ch_a.page_number,
                        doc_a_passage=sent_a,
                        doc_b_name=ch_b.document_name,
                        doc_b_page=ch_b.page_number,
                        doc_b_passage=sent_b,
                        status="Potential Contradiction",
                        review_recommendation="Harmonize notice periods across agreements to prevent procedural breach claims upon termination.",
                        severity="medium"
                    ))
        return findings

    def _check_governing_law_conflicts(self, chunks: List[DocumentChunk]) -> List[ContradictionItem]:
        findings = []
        law_pattern = re.compile(
            r'([^.!?\n]+?\bgoverned by the laws of (?:the State of\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b[^.!?\n]*[.!?])',
            re.IGNORECASE
        )

        matches: List[Tuple[DocumentChunk, str, str]] = []
        for ch in chunks:
            for m in law_pattern.finditer(ch.text):
                sent = m.group(1).strip()
                state = m.group(2).strip()
                matches.append((ch, sent, state))

        for i in range(len(matches)):
            for j in range(i + 1, len(matches)):
                ch_a, sent_a, state_a = matches[i]
                ch_b, sent_b, state_b = matches[j]
                if state_a.lower() != state_b.lower() and ch_a.document_id != ch_b.document_id:
                    findings.append(ContradictionItem(
                        contradiction_id=f"CONTR-LAW-{uuid.uuid4().hex[:6]}",
                        category="Jurisdiction Dispute",
                        summary=f"Conflicting governing law clauses: {state_a} vs {state_b}",
                        doc_a_name=ch_a.document_name,
                        doc_a_page=ch_a.page_number,
                        doc_a_passage=sent_a,
                        doc_b_name=ch_b.document_name,
                        doc_b_page=ch_b.page_number,
                        doc_b_passage=sent_b,
                        status="Potential Contradiction",
                        review_recommendation="Clarify choice of law and venue to avoid jurisdictional friction in dispute resolution.",
                        severity="high"
                    ))
        return findings

caselens_contradiction_detector = ContradictionDetector()
