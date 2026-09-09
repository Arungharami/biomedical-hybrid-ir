"""Biomedical dense retrieval (M4): ncbi/MedCPT-Query-Encoder + ncbi/MedCPT-Article-Encoder.

Config: ``configs/medcpt.yaml -> model``. Details verified against the
official model cards (see ``docs/models.md``), not assumed:

- Pooling: **CLS** -- ``last_hidden_state[:, 0, :]`` -- for both encoders.
  Unlike BGE (:mod:`biomedical_ir.dense`), MedCPT is loaded with raw
  ``transformers.AutoModel`` rather than sentence-transformers, so pooling
  is implemented explicitly here.
- Normalization: **none**. Similarity is the raw dot product; MedCPT's
  own model cards do not normalize, so :class:`biomedical_ir.faiss_index.FaissDenseIndex`
  (``IndexFlatIP``) is fed un-normalized vectors here -- inner product on
  un-normalized vectors, not cosine similarity.
- Query max length: 64 tokens. Article max length: 512 tokens.
- Article input: tokenized as a ``[title, text]`` pair, i.e.
  ``tokenizer(text=titles, text_pair=texts, ...)`` -- empirically confirmed
  to produce identical ``input_ids`` to the model card's
  ``tokenizer(list_of_[title,text]_pairs, ...)`` invocation (see the
  MedCPT section of ``docs/models.md``), so the two-list form is used here
  since it composes more naturally with this project's
  ``{doc_id: {"title":..., "text":...}}`` corpus representation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .faiss_index import FaissDenseIndex
from .utils import detect_device


@dataclass
class MedCPTConfig:
    query_encoder: str = "ncbi/MedCPT-Query-Encoder"
    article_encoder: str = "ncbi/MedCPT-Article-Encoder"
    query_max_length: int = 64
    article_max_length: int = 512
    batch_size: int = 32
    top_k: int = 100

    @classmethod
    def from_config(cls, cfg: dict[str, Any]) -> MedCPTConfig:
        m = cfg.get("model", {})
        r = cfg.get("retrieval", {})
        d = cfg.get("device", {})
        defaults = cls()
        return cls(
            query_encoder=m.get("query_encoder", defaults.query_encoder),
            article_encoder=m.get("article_encoder", defaults.article_encoder),
            query_max_length=m.get("query_max_length", defaults.query_max_length),
            article_max_length=m.get("article_max_length", defaults.article_max_length),
            batch_size=d.get("batch_size", defaults.batch_size),
            top_k=r.get("top_k", defaults.top_k),
        )


class MedCPTRetriever:
    """Two-tower biomedical retriever: separate query and article encoders.

    Interface (``build_index`` / ``rank_all``) is structurally parallel to
    :class:`biomedical_ir.dense.DenseRetriever` so both can be driven by
    identical evaluation code, despite MedCPT's two-encoder, raw-transformers
    implementation being architecturally different under the hood.
    """

    def __init__(self, config: MedCPTConfig | None = None, device: str | None = None):
        # Imported lazily so this module is importable without torch unless
        # a MedCPTRetriever is actually instantiated.
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.config = config or MedCPTConfig()
        self.device = device or detect_device()
        self._torch = torch

        self.query_tokenizer = AutoTokenizer.from_pretrained(self.config.query_encoder)
        self.query_model = AutoModel.from_pretrained(self.config.query_encoder).to(self.device).eval()

        self.article_tokenizer = AutoTokenizer.from_pretrained(self.config.article_encoder)
        self.article_model = (
            AutoModel.from_pretrained(self.config.article_encoder).to(self.device).eval()
        )

        self.doc_ids: list[str] = []
        self.index: FaissDenseIndex | None = None

    def _encode_batches(self, model, tokenizer, encode_fn, items: list, batch_size: int) -> np.ndarray:
        torch = self._torch
        all_embeddings = []
        with torch.no_grad():
            for start in range(0, len(items), batch_size):
                batch = items[start : start + batch_size]
                encoded = encode_fn(tokenizer, batch).to(self.device)
                outputs = model(**encoded)
                cls_embeddings = outputs.last_hidden_state[:, 0, :]  # [CLS] pooling, per model card
                all_embeddings.append(cls_embeddings.cpu().numpy())
        return np.concatenate(all_embeddings, axis=0) if all_embeddings else np.zeros((0, 768))

    def _tokenize_queries(self, tokenizer, batch: list[str]):
        return tokenizer(
            batch,
            truncation=True,
            padding=True,
            return_tensors="pt",
            max_length=self.config.query_max_length,
        )

    def _tokenize_articles(self, tokenizer, batch: list[tuple[str, str]]):
        titles = [t for t, _ in batch]
        texts = [t for _, t in batch]
        return tokenizer(
            text=titles,
            text_pair=texts,
            truncation=True,
            padding=True,
            return_tensors="pt",
            max_length=self.config.article_max_length,
        )

    def encode_documents(self, corpus: dict[str, dict[str, str]]) -> np.ndarray:
        """``corpus`` maps doc_id -> {"title": str, "text": str} (NOT a pre-composed string --
        MedCPT's article encoder consumes title/text as a structured pair, unlike TF-IDF/BM25/BGE
        which use ``compose_document_text``)."""
        self.doc_ids = list(corpus.keys())
        pairs = [(corpus[d].get("title", ""), corpus[d].get("text", "")) for d in self.doc_ids]
        return self._encode_batches(
            self.article_model,
            self.article_tokenizer,
            self._tokenize_articles,
            pairs,
            self.config.batch_size,
        )

    def build_index(self, corpus: dict[str, dict[str, str]]) -> np.ndarray:
        embeddings = self.encode_documents(corpus)
        self.index = FaissDenseIndex.build(self.doc_ids, embeddings)
        return embeddings

    def encode_queries(self, queries: dict[str, str]) -> tuple[list[str], np.ndarray]:
        qids = list(queries.keys())
        texts = [queries[q] for q in qids]
        embeddings = self._encode_batches(
            self.query_model,
            self.query_tokenizer,
            self._tokenize_queries,
            texts,
            self.config.batch_size,
        )
        return qids, embeddings

    def rank_all(
        self, queries: dict[str, str], top_k: int | None = None
    ) -> dict[str, list[tuple[str, float]]]:
        if self.index is None:
            raise RuntimeError("MedCPTRetriever.build_index() must be called before rank_all().")
        top_k = top_k if top_k is not None else self.config.top_k
        qids, q_embeddings = self.encode_queries(queries)
        results = self.index.search(q_embeddings, top_k)
        return dict(zip(qids, results))
