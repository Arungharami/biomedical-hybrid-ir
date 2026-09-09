"""FAISS index wrapper for dense retrieval (M3/M4).

Uses ``IndexFlatIP`` (exact inner-product search) per ``configs/bge.yaml``
and ``configs/medcpt.yaml``. NFCorpus's corpus (3,633 docs) is small enough
that approximate indexing (IVF/HNSW) is unnecessary; exact search keeps
retrieval deterministic and removes approximation error as a confound in the
model-vs-model effectiveness comparison this project is built around.

Inner product over L2-normalized embeddings (BGE) is equivalent to cosine
similarity; MedCPT is not normalized by design (its model card specifies raw
dot-product similarity), so ``IndexFlatIP`` is used unmodified for both —
the "cosine vs dot" distinction lives entirely in whether embeddings were
normalized before being added to the index, not in the index type itself.
"""

from __future__ import annotations

from dataclasses import dataclass

import faiss
import numpy as np


@dataclass
class FaissDenseIndex:
    doc_ids: list[str]
    index: faiss.Index

    @classmethod
    def build(cls, doc_ids: list[str], embeddings: np.ndarray) -> FaissDenseIndex:
        if len(doc_ids) != embeddings.shape[0]:
            raise ValueError(
                f"doc_ids length ({len(doc_ids)}) != embeddings rows ({embeddings.shape[0]})"
            )
        embeddings = np.ascontiguousarray(embeddings, dtype="float32")
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)
        return cls(doc_ids=list(doc_ids), index=index)

    def search(self, query_embeddings: np.ndarray, top_k: int) -> list[list[tuple[str, float]]]:
        """Return, per query row, a list of (doc_id, score) sorted by descending score."""
        query_embeddings = np.ascontiguousarray(query_embeddings, dtype="float32")
        if query_embeddings.ndim == 1:
            query_embeddings = query_embeddings.reshape(1, -1)
        k = min(top_k, len(self.doc_ids))
        scores, indices = self.index.search(query_embeddings, k)
        results: list[list[tuple[str, float]]] = []
        for score_row, idx_row in zip(scores, indices):
            results.append(
                [(self.doc_ids[i], float(s)) for s, i in zip(score_row, idx_row) if i != -1]
            )
        return results

    @property
    def ntotal(self) -> int:
        return self.index.ntotal

    @property
    def dim(self) -> int:
        return self.index.d

    def index_size_bytes(self) -> int:
        """Approximate resident size of a flat float32 index: ntotal * dim * 4 bytes."""
        return self.index.ntotal * self.index.d * 4
