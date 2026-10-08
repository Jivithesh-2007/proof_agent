import hashlib
from typing import List, Optional, Any

class EmbeddingService:
    """Service providing vector embeddings deterministically without external model servers."""

    def __init__(self, provider: Optional[Any] = None):
        self.provider = provider

    def _hash_embed(self, text: str, dim: int = 128) -> List[float]:
        """Generates deterministic pseudo-embedding vector from text hash."""
        vec = []
        for i in range(dim):
            h = hashlib.sha256(f"{text}_{i}".encode('utf-8')).hexdigest()
            val = (int(h[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
            vec.append(round(val, 6))
        return vec

    def embed_query(self, query: str) -> List[float]:
        if self.provider and hasattr(self.provider, "embed_text"):
            return self.provider.embed_text(query)
        return self._hash_embed(query)

    def embed_chunks(self, texts: List[str]) -> List[List[float]]:
        if self.provider and hasattr(self.provider, "embed_batch"):
            return self.provider.embed_batch(texts)
        return [self._hash_embed(t) for t in texts]
