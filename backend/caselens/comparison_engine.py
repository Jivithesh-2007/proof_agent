"""Document Comparison Engine for CaseLens AI."""
import re
import difflib
from typing import List, Dict, Any, Optional
from backend.caselens.models import (
    DocumentComparisonResponse,
    ClauseComparisonItem,
    DocumentChunk,
)
from backend.caselens.storage import caselens_storage

class DocumentComparator:
    """
    Compares two documents side-by-side:
    - Analyzes added, removed, and modified sections.
    - Highlights changed dates, figures, and obligations.
    - Computes structural similarity scores.
    """

    def compare_documents(self, doc_a_id: str, doc_b_id: str) -> DocumentComparisonResponse:
        doc_a = caselens_storage.get_document(doc_a_id)
        doc_b = caselens_storage.get_document(doc_b_id)

        if not doc_a or not doc_b:
            raise ValueError(f"One or both documents ({doc_a_id}, {doc_b_id}) not found.")

        chunks_a = caselens_storage.get_document_chunks(doc_a_id)
        chunks_b = caselens_storage.get_document_chunks(doc_b_id)

        text_a = "\n\n".join(c.text for c in chunks_a)
        text_b = "\n\n".join(c.text for c in chunks_b)

        # Break into paragraphs
        paras_a = [p.strip() for p in text_a.split("\n\n") if p.strip()]
        paras_b = [p.strip() for p in text_b.split("\n\n") if p.strip()]

        clause_comparisons: List[ClauseComparisonItem] = []
        key_differences: List[str] = []

        added_cnt = 0
        removed_cnt = 0
        modified_cnt = 0

        # Pair paragraphs using difflib SequenceMatcher
        matcher = difflib.SequenceMatcher(None, paras_a, paras_b)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for idx in range(i1, i2):
                    p_text = paras_a[idx]
                    clause_comparisons.append(ClauseComparisonItem(
                        section_title=self._guess_title(p_text),
                        change_type="identical",
                        doc_a_text=p_text,
                        doc_b_text=p_text,
                        observation="Identical clause in both documents."
                    ))
            elif tag == 'replace':
                for a_idx, b_idx in zip(range(i1, i2), range(j1, j2)):
                    p_a = paras_a[a_idx]
                    p_b = paras_b[b_idx]
                    modified_cnt += 1
                    diff_obs = self._detect_specific_changes(p_a, p_b)
                    clause_comparisons.append(ClauseComparisonItem(
                        section_title=self._guess_title(p_a),
                        change_type="modified",
                        doc_a_text=p_a,
                        doc_b_text=p_b,
                        observation=diff_obs
                    ))
                    key_differences.append(diff_obs)
            elif tag == 'delete':
                for idx in range(i1, i2):
                    p_text = paras_a[idx]
                    removed_cnt += 1
                    clause_comparisons.append(ClauseComparisonItem(
                        section_title=self._guess_title(p_text),
                        change_type="removed_in_b",
                        doc_a_text=p_text,
                        doc_b_text=None,
                        observation="Clause present in Document A but omitted in Document B."
                    ))
                    key_differences.append(f"Omission in {doc_b.filename}: '{self._guess_title(p_text)}' clause removed.")
            elif tag == 'insert':
                for idx in range(j1, j2):
                    p_text = paras_b[idx]
                    added_cnt += 1
                    clause_comparisons.append(ClauseComparisonItem(
                        section_title=self._guess_title(p_text),
                        change_type="added_in_b",
                        doc_a_text=None,
                        doc_b_text=p_text,
                        observation="New clause introduced in Document B."
                    ))
                    key_differences.append(f"New provision in {doc_b.filename}: '{self._guess_title(p_text)}' added.")

        # Overall text similarity
        overall_similarity = round(difflib.SequenceMatcher(None, text_a, text_b).ratio() * 100, 1)

        return DocumentComparisonResponse(
            doc_a_id=doc_a_id,
            doc_a_name=doc_a.filename,
            doc_b_id=doc_b_id,
            doc_b_name=doc_b.filename,
            similarity_score=overall_similarity,
            added_clauses=added_cnt,
            removed_clauses=removed_cnt,
            modified_clauses=modified_cnt,
            clause_comparisons=clause_comparisons[:30],
            key_differences=key_differences[:10]
        )

    def _guess_title(self, paragraph: str) -> str:
        lines = paragraph.split("\n")
        first_line = lines[0].strip()
        if len(first_line) < 60:
            return first_line
        words = first_line.split()
        return " ".join(words[:6]) + "..."

    def _detect_specific_changes(self, text_a: str, text_b: str) -> str:
        # Check monetary change
        money_a = re.findall(r'\$\s?[\d,]+(?:\.\d{2})?', text_a)
        money_b = re.findall(r'\$\s?[\d,]+(?:\.\d{2})?', text_b)
        if money_a and money_b and money_a != money_b:
            return f"Monetary amendment: {', '.join(money_a)} changed to {', '.join(money_b)}."

        # Check date change
        date_a = re.findall(r'\b(?:\d{1,2}\s+[A-Z][a-z]+\s+\d{4}|[A-Z][a-z]+\s+\d{1,2},?\s+\d{4})\b', text_a)
        date_b = re.findall(r'\b(?:\d{1,2}\s+[A-Z][a-z]+\s+\d{4}|[A-Z][a-z]+\s+\d{1,2},?\s+\d{4})\b', text_b)
        if date_a and date_b and date_a != date_b:
            return f"Date modification: '{date_a[0]}' replaced with '{date_b[0]}'."

        return "Substantive phrasing or obligation wording modified between versions."

caselens_comparator = DocumentComparator()
