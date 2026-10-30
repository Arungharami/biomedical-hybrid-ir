"""Live, single-query search engine used by the CAP 6776 interactive demo.

This module wires the *same* library components used for the recorded
experiments (BM25, MedCPT + FAISS, RRF, MedCPT cross-encoder) into one
object that answers an arbitrary typed query. It adds no new ranking logic:

    BM25 ............ biomedical_ir.bm25.BM25Retriever.rank
    MedCPT .......... MedCPTRetriever.rank_all  (dense two-tower + FAISS IndexFlatIP)
    Hybrid (RRF) .... biomedical_ir.fusion.reciprocal_rank_fusion, k=60
    Hybrid + Rerank . CrossEncoderReranker.rerank_query on the top-``pool`` RRF candidates

The dense retriever and reranker are injected as zero-argument factories and
built lazily on first use, so (a) BM25 answers instantly while the
transformer models load, and (b) unit tests can substitute tiny stand-ins
without downloading any model weights.

For judged NFCorpus test queries, :func:`judge_ranking` scores a live
ranking against the official qrels with the project's own metric functions
(P@10, nDCG@10, RR@10), so the demo can show evaluation happening live.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

from biomedical_ir.bm25 import BM25Retriever
from biomedical_ir.data import compose_document_text
from biomedical_ir.evaluation import ndcg_at_k, precision_at_k, reciprocal_rank
from biomedical_ir.fusion import reciprocal_rank_fusion

BM25 = "BM25"
MEDCPT = "MedCPT"
HYBRID = "Hybrid (RRF)"
RERANK = "Hybrid + Cross-Encoder"
METHODS = (BM25, MEDCPT, HYBRID, RERANK)


@dataclass
class Hit:
    rank: int
    doc_id: str
    score: float
    title: str
    snippet: str
    bm25_rank: int | None = None  # this doc's rank in BM25's list (None = not retrieved)
    dense_rank: int | None = None  # this doc's rank in MedCPT's list
    rrf_rank: int | None = None  # rank before cross-encoder reranking (rerank mode only)


@dataclass
class SearchResult:
    query: str
    method: str
    hits: list[Hit]
    latency_ms: float
    notes: list[str] = field(default_factory=list)


class LiveSearchEngine:
    def __init__(
        self,
        corpus: dict[str, dict[str, str]],
        dense_factory: Callable[[], object] | None = None,
        reranker_factory: Callable[[], object] | None = None,
        rrf_k: int = 60,
        candidate_depth: int = 100,
        snippet_chars: int = 240,
    ):
        """``corpus`` maps doc_id -> {"title", "text"} (the NFCorpus layout).

        ``dense_factory()`` must return an object with ``rank_all({qid: text}, top_k)``
        (e.g. a MedCPTRetriever whose index is built). ``reranker_factory()`` must
        return an object with ``rerank_query(query, candidates, corpus, top_k)``.
        """
        self.corpus = corpus
        self.rrf_k = rrf_k
        self.depth = candidate_depth
        self.snippet_chars = snippet_chars
        self._dense_factory = dense_factory
        self._reranker_factory = reranker_factory
        self._dense = None
        self._reranker = None
        # Inverted index is cheap (~1 s for 3,633 docs), so build it eagerly.
        self.bm25 = BM25Retriever().fit(
            {d: compose_document_text(m.get("title", ""), m.get("text", "")) for d, m in corpus.items()}
        )

    # -- lazily constructed neural components ---------------------------------
    @property
    def dense(self):
        if self._dense is None:
            if self._dense_factory is None:
                raise RuntimeError("No dense retriever configured for this engine.")
            self._dense = self._dense_factory()
        return self._dense

    @property
    def reranker(self):
        if self._reranker is None:
            if self._reranker_factory is None:
                raise RuntimeError("No cross-encoder reranker configured for this engine.")
            self._reranker = self._reranker_factory()
        return self._reranker

    # -- component rankings ---------------------------------------------------
    def bm25_ranking(self, query: str) -> list[tuple[str, float]]:
        return self.bm25.rank(query, top_k=self.depth)

    def dense_ranking(self, query: str) -> list[tuple[str, float]]:
        return self.dense.rank_all({"q": query}, top_k=self.depth)["q"]

    # -- main entry point -----------------------------------------------------
    def search(self, query: str, method: str = HYBRID, top_k: int = 10, pool: int = 50) -> SearchResult:
        query = (query or "").strip()
        if method not in METHODS:
            raise ValueError(f"Unknown method {method!r}; choose from {METHODS}")
        if not query:
            return SearchResult(query, method, [], 0.0, ["Empty query."])

        start = time.perf_counter()
        notes: list[str] = []
        bm25_list: list[tuple[str, float]] = []
        dense_list: list[tuple[str, float]] = []
        if method in (BM25, HYBRID, RERANK):
            bm25_list = self.bm25_ranking(query)
            if not bm25_list:
                notes.append(
                    "BM25 found no document sharing a single query term "
                    "(vocabulary mismatch) - only MedCPT can contribute."
                )
        if method in (MEDCPT, HYBRID, RERANK):
            dense_list = self.dense_ranking(query)

        bm25_pos = {d: i for i, (d, _) in enumerate(bm25_list, start=1)}
        dense_pos = {d: i for i, (d, _) in enumerate(dense_list, start=1)}
        rrf_pos: dict[str, int] = {}

        if method == BM25:
            ranked = bm25_list
        elif method == MEDCPT:
            ranked = dense_list
        else:
            # Fuse RANKS, not raw scores: on NFCorpus BM25 top scores are ~5-15
            # while MedCPT dot products are ~55-65 - incomparable scales.
            ranked = reciprocal_rank_fusion(
                [[d for d, _ in bm25_list], [d for d, _ in dense_list]], k=self.rrf_k
            )
            if method == RERANK:
                candidates = ranked[:pool]
                rrf_pos = {d: i for i, (d, _) in enumerate(candidates, start=1)}
                ranked = self.reranker.rerank_query(query, candidates, self.corpus, top_k=pool)
                notes.append(
                    f"Cross-encoder re-scored the top {len(candidates)} RRF candidates; "
                    "it cannot surface documents outside that pool."
                )

        latency_ms = (time.perf_counter() - start) * 1000.0
        hits = [
            Hit(
                rank=i,
                doc_id=d,
                score=float(s),
                title=self.corpus.get(d, {}).get("title", ""),
                snippet=self._snippet(d),
                bm25_rank=bm25_pos.get(d),
                dense_rank=dense_pos.get(d),
                rrf_rank=rrf_pos.get(d),
            )
            for i, (d, s) in enumerate(ranked[:top_k], start=1)
        ]
        return SearchResult(query, method, hits, latency_ms, notes)

    def _snippet(self, doc_id: str) -> str:
        text = self.corpus.get(doc_id, {}).get("text", "")
        if len(text) <= self.snippet_chars:
            return text
        return text[: self.snippet_chars].rsplit(" ", 1)[0] + " ..."


def judge_ranking(doc_ids: list[str], qrels_for_query: dict[str, int], k: int = 10) -> dict[str, float]:
    """Score one ranking against one query's graded qrels (0/1/2) with the
    project's own metric implementations (validated against pytrec_eval in tests)."""
    return {
        f"P@{k}": precision_at_k(doc_ids, qrels_for_query, k),
        f"nDCG@{k}": ndcg_at_k(doc_ids, qrels_for_query, k),
        f"RR@{k}": reciprocal_rank(doc_ids, qrels_for_query, k),
        "judged_relevant": float(sum(1 for g in qrels_for_query.values() if g > 0)),
    }
