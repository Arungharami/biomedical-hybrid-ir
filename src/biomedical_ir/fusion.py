"""Reciprocal Rank Fusion (M5): combine BM25 + MedCPT rankings.

    RRF(d) = sum_i 1 / (k + rank_i(d))

``rank_i(d)`` is the 1-indexed rank of document ``d`` in retriever ``i``'s
ranking; a document absent from a component's ranking simply contributes 0
from that component (it is not penalized with an artificial worst-rank).
Default ``k=60``, per Cormack, Clarke & Buettcher (2009), configurable via
``configs/hybrid.yaml -> fusion.k``.

RRF is deliberately defined over RANK POSITIONS, not raw retrieval scores:
BM25 scores are unbounded and MedCPT similarities are raw (unnormalized)
dot products, so the two live on incomparable scales. Summing them directly
would implicitly and arbitrarily weight whichever retriever happens to
produce larger-magnitude scores, not whichever is more accurate — see
``docs/architecture.md`` for the full rationale.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RunType = dict[str, list[tuple[str, float]]]


@dataclass
class RRFConfig:
    k: int = 60
    candidate_depth: int = 100
    top_k: int = 100

    @classmethod
    def from_config(cls, cfg: dict[str, Any]) -> RRFConfig:
        f = cfg.get("fusion", {})
        r = cfg.get("retrieval", {})
        defaults = cls()
        return cls(
            k=f.get("k", defaults.k),
            candidate_depth=r.get("candidate_depth", defaults.candidate_depth),
            top_k=r.get("top_k", defaults.top_k),
        )


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """Fuse multiple ranked doc-id lists (best-first) for ONE query via RRF.

    ``rankings`` is a list of ranked doc-id lists, one per retrieval
    component (e.g. ``[bm25_doc_ids, medcpt_doc_ids]``). Returns
    ``(doc_id, rrf_score)`` pairs sorted by descending score, ties broken by
    ascending doc_id for determinism.
    """
    if k <= 0:
        raise ValueError("k must be positive")
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def fuse_runs(
    runs: list[RunType],
    k: int = 60,
    candidate_depth: int = 100,
    top_k: int = 100,
) -> RunType:
    """Fuse multiple component runs (each ``{qid: [(doc_id, score), ...]}``) via RRF.

    Only the top ``candidate_depth`` documents of each component run
    contribute to a query's fusion (matching
    ``configs/hybrid.yaml -> retrieval.candidate_depth``). The fused output
    covers the UNION of query IDs across all component runs -- a query
    missing from one component simply receives no contribution from it,
    rather than being dropped from the fused output entirely.
    """
    if k <= 0:
        raise ValueError("k must be positive")
    all_qids: set[str] = set()
    for run in runs:
        all_qids.update(run.keys())

    fused: RunType = {}
    for qid in all_qids:
        rankings = [[doc_id for doc_id, _ in run.get(qid, [])[:candidate_depth]] for run in runs]
        fused_scores = reciprocal_rank_fusion(rankings, k=k)
        fused[qid] = fused_scores[:top_k]
    return fused
