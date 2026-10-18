"""Modular, local-first retriever for CaseLens AI."""
import math
import re
from typing import List, Tuple
from backend.caselens.models import DocumentChunk, Citation

STOPWORDS = {
    "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does",
    "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until",
    "while", "of", "at", "by", "for", "with", "about", "against", "between", "into",
    "through", "during", "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now", "clause", "document"
}

class LocalEvidenceRetriever:
    """
    Deterministic hybrid BM25 / token-matching retriever for legal document intelligence.
    Runs locally with zero external network or GPU requirement.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r'\b[a-zA-Z0-9_]{2,}\b', text)]

    def retrieve(
        self,
        query: str,
        chunks: List[DocumentChunk],
        top_k: int = 5,
        min_score: float = 0.5
    ) -> List[Tuple[DocumentChunk, float, str]]:
        """
        Returns list of (DocumentChunk, score, matched_passage_snippet).
        """
        if not chunks:
            return []

        all_query_tokens = self._tokenize(query)
        # Content query tokens excluding common stopwords
        content_query_tokens = [t for t in all_query_tokens if t not in STOPWORDS]
        query_tokens = content_query_tokens if content_query_tokens else all_query_tokens
        if not query_tokens:
            return []

        # Corpus stats
        doc_count = len(chunks)
        chunk_token_lists = [self._tokenize(c.text) for c in chunks]
        doc_lens = [len(toks) for toks in chunk_token_lists]
        avg_doc_len = sum(doc_lens) / max(1, doc_count)

        # IDF calculation
        idf: dict[str, float] = {}
        for token in query_tokens:
            n_q = sum(1 for toks in chunk_token_lists if token in toks)
            # Standard BM25 IDF
            idf[token] = math.log((doc_count - n_q + 0.5) / (n_q + 0.5) + 1.0)

        # Score chunks
        scored_results: List[Tuple[DocumentChunk, float, str]] = []
        for i, chunk in enumerate(chunks):
            tokens = chunk_token_lists[i]
            doc_len = doc_lens[i]
            if doc_len == 0:
                continue

            score = 0.0
            term_freqs: dict[str, int] = {}
            for t in tokens:
                term_freqs[t] = term_freqs.get(t, 0) + 1

            for q_term in query_tokens:
                f_q = term_freqs.get(q_term, 0)
                if f_q > 0:
                    numerator = f_q * (self.k1 + 1.0)
                    denominator = f_q + self.k1 * (1.0 - self.b + self.b * (doc_len / avg_doc_len))
                    score += idf.get(q_term, 0.0) * (numerator / denominator)

            # Boost exact phrase matches
            clean_query = query.lower().strip()
            if len(clean_query) > 6 and clean_query in chunk.text.lower():
                score += 5.0

            # Boost key legal keywords (e.g. termination, notice, penalty, payment, liability, governing)
            for kw in ["terminate", "termination", "payment", "liability", "breach", "indemnify", "confidential", "governing", "jurisdiction", "obligation"]:
                if kw in query_tokens and kw in tokens:
                    score += 0.8

            matched_content_tokens = sum(1 for q in query_tokens if term_freqs.get(q, 0) > 0)
            token_match_ratio = matched_content_tokens / max(1, len(query_tokens))

            # If question has multiple content words, require at least 2 words or 50% match
            if len(query_tokens) >= 3 and (matched_content_tokens < 2 or token_match_ratio < 0.35):
                continue

            if score >= min_score and matched_content_tokens >= 1:
                # Find most relevant sentence snippet
                sentences = re.split(r'(?<=[.!?])\s+', chunk.text)
                best_snippet = chunk.text[:250]
                best_s_score = 0
                for s in sentences:
                    s_score = sum(1 for q in query_tokens if q in s.lower())
                    if s_score > best_s_score:
                        best_s_score = s_score
                        best_snippet = s.strip()

                scored_results.append((chunk, score, best_snippet))

        # Sort descending by score
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:top_k]

    def build_citations(self, scored_chunks: List[Tuple[DocumentChunk, float, str]]) -> List[Citation]:
        citations = []
        for i, (chunk, score, snippet) in enumerate(scored_chunks):
            # Extract sentence or clean passage
            clean_snippet = snippet.strip()
            if len(clean_snippet) > 300:
                clean_snippet = clean_snippet[:297] + "..."

            cit_id = f"CIT-{i+1}"
            citations.append(Citation(
                citation_id=cit_id,
                document_id=chunk.document_id,
                document_name=chunk.document_name,
                page_number=chunk.page_number,
                section=chunk.section_heading,
                quoted_text=clean_snippet,
                char_start=chunk.char_start,
                char_end=chunk.char_end,
                confidence_score=round(min(1.0, score / 10.0), 2),
                verification_status="supported",
                validation_note="Direct match from extracted document text."
            ))
        return citations

caselens_retriever = LocalEvidenceRetriever()
