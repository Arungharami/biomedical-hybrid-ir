"""Deterministic candidate-truncated RRF and query-wise min-max score fusion."""

from __future__ import annotations

import math

from .fusion import fuse_runs


def validate_run(run, query_ids, document_ids):
    if set(run) != set(query_ids):
        raise ValueError("Runs must cover exactly the declared query population")
    for ranking in run.values():
        ids = [d for d, _ in ranking]
        if len(ids) != len(set(ids)) or set(ids) - set(document_ids):
            raise ValueError("Duplicate or unknown document IDs")
        scores = [float(s) for _, s in ranking]
        if any(not math.isfinite(s) for s in scores):
            raise ValueError("Nonfinite retrieval scores")
        if scores != sorted(scores, reverse=True):
            raise ValueError("Runs must be sorted by descending score")


def weighted_fusion(lexical, dense, alpha=0.5, depth=100, top_k=100):
    if not 0 <= alpha <= 1 or depth <= 0 or top_k <= 0:
        raise ValueError("Invalid fusion weight or candidate budget")
    fused = {}
    for qid in sorted(set(lexical) | set(dense)):
        # Endpoints reproduce the active component including its tie order.
        if alpha in (0, 1):
            source = lexical if alpha == 1 else dense
            fused[qid] = list(source.get(qid, [])[:min(depth, top_k)])
            continue
        scores = {}
        for source, weight in ((lexical, alpha), (dense, 1 - alpha)):
            ranking = source.get(qid, [])[:depth]
            if not ranking:
                continue
            values = [float(s) for _, s in ranking]
            low, high = min(values), max(values)
            for doc, score in ranking:
                # Equal-score observed documents receive 1; absent docs receive 0.
                value = (score - low) / (high - low) if high > low else 1.0
                scores[doc] = scores.get(doc, 0) + weight * value
        fused[qid] = sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:top_k]
    return fused


def combine(lexical, dense, method, parameter, depth=100):
    if method == "rrf":
        return fuse_runs([lexical, dense], k=int(parameter), candidate_depth=depth, top_k=depth)
    if method == "weighted":
        return weighted_fusion(lexical, dense, alpha=parameter, depth=depth, top_k=depth)
    raise ValueError(f"Unknown fusion method: {method}")
