"""Biomedical cross-encoder reranking (M6): ncbi/MedCPT-Cross-Encoder.

Config: ``configs/reranker.yaml -> reranker``. Details verified against the
official model card (see ``docs/models.md``), not assumed:

- Input: ``[query, article]`` pairs, tokenized jointly as
  ``tokenizer(text=queries, text_pair=articles, ...)`` -- empirically
  confirmed to produce identical ``input_ids`` to the model card's
  ``tokenizer(list_of_[query,article]_pairs, ...)`` invocation (see
  ``docs/models.md``).
- ``article`` = ``"{title}. {text}"`` (title and body joined with a period
  and space), per ``article_join`` in ``configs/reranker.yaml`` -- the join
  convention used in the official MedCPT reference code.
- Output: a single raw logit per pair (``AutoModelForSequenceClassification``,
  ``num_labels=1``); higher = more relevant. No sigmoid is applied for
  ranking, since only relative order matters.
- Max sequence length: 512.

The reranker is applied to a bounded CANDIDATE POOL per query (default 50,
configurable: 20/50/100 tested as ablation A6), not the full corpus -- see
Section 11 of the project spec: cross-encoder scoring over the entire
corpus is an explicit, separate efficiency experiment, not the default
pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .utils import detect_device

RunType = dict[str, list[tuple[str, float]]]


@dataclass
class RerankerConfig:
    model: str = "ncbi/MedCPT-Cross-Encoder"
    article_join: str = "{title}. {text}"
    candidate_pool: int = 50
    max_length: int = 512
    batch_size: int = 32
    top_k: int = 100

    @classmethod
    def from_config(cls, cfg: dict[str, Any]) -> RerankerConfig:
        r = cfg.get("reranker", {})
        d = cfg.get("device", {})
        rt = cfg.get("retrieval", {})
        defaults = cls()
        return cls(
            model=r.get("model", defaults.model),
            article_join=r.get("article_join", defaults.article_join),
            candidate_pool=r.get("default_candidate_pool", defaults.candidate_pool),
            max_length=r.get("max_length", defaults.max_length),
            batch_size=d.get("batch_size", defaults.batch_size),
            top_k=rt.get("top_k", defaults.top_k),
        )


def format_article(title: str, text: str, template: str = "{title}. {text}") -> str:
    """Compose an article string for the cross-encoder, per ``article_join``.

    Falls back gracefully when title or text is empty, mirroring
    :func:`biomedical_ir.data.compose_document_text`'s handling (never
    produces a leading/trailing "``. ``" artifact from a missing field).
    """
    title = (title or "").strip()
    text = (text or "").strip()
    if title and text:
        return template.format(title=title, text=text)
    return title or text


class CrossEncoderReranker:
    """Scores (query, article) pairs with a cross-encoder and reorders a candidate pool."""

    def __init__(self, config: RerankerConfig | None = None, device: str | None = None):
        # Imported lazily so this module is importable without torch unless
        # a CrossEncoderReranker is actually instantiated.
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.config = config or RerankerConfig()
        self.device = device or detect_device()
        self._torch = torch

        self.tokenizer = AutoTokenizer.from_pretrained(self.config.model)
        self.model = (
            AutoModelForSequenceClassification.from_pretrained(self.config.model)
            .to(self.device)
            .eval()
        )

    def score_pairs(self, queries: list[str], articles: list[str]) -> list[float]:
        """Score parallel lists of (query, article) pairs; returns raw logits."""
        if len(queries) != len(articles):
            raise ValueError("queries and articles must be the same length")
        torch = self._torch
        all_scores: list[float] = []
        with torch.no_grad():
            for start in range(0, len(queries), self.config.batch_size):
                q_batch = queries[start : start + self.config.batch_size]
                a_batch = articles[start : start + self.config.batch_size]
                encoded = self.tokenizer(
                    text=q_batch,
                    text_pair=a_batch,
                    truncation=True,
                    padding=True,
                    return_tensors="pt",
                    max_length=self.config.max_length,
                ).to(self.device)
                logits = self.model(**encoded).logits.squeeze(dim=1)
                all_scores.extend(logits.cpu().tolist())
        return all_scores

    def rerank_query(
        self,
        query: str,
        candidates: list[tuple[str, str]],
        corpus: dict[str, dict[str, str]],
        top_k: int | None = None,
    ) -> list[tuple[str, float]]:
        """Rerank one query's candidate pool.

        ``candidates`` is ``[(doc_id, prior_score), ...]`` from an upstream
        run (e.g. hybrid RRF); only doc IDs are used here (RRF scores are
        rank-based and not comparable to cross-encoder logits, so they are
        discarded rather than combined). ``corpus`` supplies title/text for
        formatting via :func:`format_article`.
        """
        top_k = top_k if top_k is not None else self.config.top_k
        doc_ids = [d for d, _ in candidates]
        articles = [
            format_article(
                corpus.get(d, {}).get("title", ""),
                corpus.get(d, {}).get("text", ""),
                self.config.article_join,
            )
            for d in doc_ids
        ]
        scores = self.score_pairs([query] * len(doc_ids), articles)
        ranked = sorted(zip(doc_ids, scores), key=lambda kv: (-kv[1], kv[0]))
        return ranked[:top_k]

    def rerank_run(
        self,
        run: RunType,
        queries: dict[str, str],
        corpus: dict[str, dict[str, str]],
        candidate_pool: int | None = None,
        top_k: int | None = None,
    ) -> RunType:
        """Rerank every query in ``run`` (e.g. the hybrid RRF run), truncating each
        query's candidates to ``candidate_pool`` before scoring."""
        candidate_pool = candidate_pool if candidate_pool is not None else self.config.candidate_pool
        reranked: RunType = {}
        for qid, doc_scores in run.items():
            if qid not in queries:
                continue
            candidates = doc_scores[:candidate_pool]
            reranked[qid] = self.rerank_query(queries[qid], candidates, corpus, top_k=top_k)
        return reranked
