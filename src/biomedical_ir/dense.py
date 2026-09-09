"""General-purpose dense retrieval (M3): BAAI/bge-base-en-v1.5.

Config: ``configs/bge.yaml -> model`` (name, query_instruction,
document_instruction, normalize_embeddings, max_seq_length, embedding_dim)
and ``-> faiss.index_type``. Details verified against the official model
card (see ``docs/models.md``), not assumed:

- Pooling: CLS -- handled internally by this checkpoint's bundled
  sentence-transformers Pooling module, so no manual pooling code is needed
  here (unlike MedCPT in :mod:`biomedical_ir.medcpt`, which uses raw
  ``transformers`` and pools ``last_hidden_state[:, 0, :]`` explicitly).
- Normalization: L2-normalized embeddings (``normalize_embeddings=True``).
- Instruction: ``query_instruction`` is prepended to queries only, never to
  documents, per the model card.
- Similarity: cosine == inner product on normalized embeddings, so
  :class:`biomedical_ir.faiss_index.FaissDenseIndex` (``IndexFlatIP``) is
  used as-is.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .faiss_index import FaissDenseIndex
from .utils import detect_device


@dataclass
class DenseModelConfig:
    name: str = "BAAI/bge-base-en-v1.5"
    query_instruction: str = "Represent this sentence for searching relevant passages: "
    document_instruction: str = ""
    normalize_embeddings: bool = True
    max_seq_length: int = 512
    embedding_dim: int = 768
    batch_size: int = 32
    top_k: int = 100

    @classmethod
    def from_config(cls, cfg: dict[str, Any]) -> DenseModelConfig:
        m = cfg.get("model", {})
        r = cfg.get("retrieval", {})
        d = cfg.get("device", {})
        defaults = cls()
        return cls(
            name=m.get("name", defaults.name),
            query_instruction=m.get("query_instruction", defaults.query_instruction),
            document_instruction=m.get("document_instruction", defaults.document_instruction),
            normalize_embeddings=m.get("normalize_embeddings", defaults.normalize_embeddings),
            max_seq_length=m.get("max_seq_length", defaults.max_seq_length),
            embedding_dim=m.get("embedding_dim", defaults.embedding_dim),
            batch_size=d.get("batch_size", defaults.batch_size),
            top_k=r.get("top_k", defaults.top_k),
        )


class DenseRetriever:
    """Bi-encoder dense retriever for a single sentence-transformers checkpoint.

    Structurally parallel to :class:`biomedical_ir.medcpt.MedCPTRetriever`
    (same ``build_index`` / ``rank_all`` interface) so both can be driven by
    identical scripts/evaluation code, even though MedCPT uses two distinct
    encoders and raw ``transformers`` internally rather than one
    sentence-transformers checkpoint.
    """

    def __init__(self, config: DenseModelConfig | None = None, device: str | None = None):
        # Imported lazily so importing this module doesn't require torch to be
        # installed unless a DenseRetriever is actually instantiated.
        from sentence_transformers import SentenceTransformer

        self.config = config or DenseModelConfig()
        self.device = device or detect_device()
        self.model = SentenceTransformer(self.config.name, device=self.device)
        self.model.max_seq_length = self.config.max_seq_length
        self.doc_ids: list[str] = []
        self.index: FaissDenseIndex | None = None

    def _encode(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(
            texts,
            batch_size=self.config.batch_size,
            normalize_embeddings=self.config.normalize_embeddings,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

    def encode_documents(self, corpus: dict[str, str]) -> np.ndarray:
        self.doc_ids = list(corpus.keys())
        texts = [self.config.document_instruction + corpus[d] for d in self.doc_ids]
        return self._encode(texts)

    def build_index(self, corpus: dict[str, str]) -> np.ndarray:
        embeddings = self.encode_documents(corpus)
        self.index = FaissDenseIndex.build(self.doc_ids, embeddings)
        return embeddings

    def encode_queries(self, queries: dict[str, str]) -> tuple[list[str], np.ndarray]:
        qids = list(queries.keys())
        texts = [self.config.query_instruction + queries[q] for q in qids]
        return qids, self._encode(texts)

    def rank_all(
        self, queries: dict[str, str], top_k: int | None = None
    ) -> dict[str, list[tuple[str, float]]]:
        if self.index is None:
            raise RuntimeError("DenseRetriever.build_index() must be called before rank_all().")
        top_k = top_k if top_k is not None else self.config.top_k
        qids, q_embeddings = self.encode_queries(queries)
        results = self.index.search(q_embeddings, top_k)
        return dict(zip(qids, results))
