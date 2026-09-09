"""IR evaluation metrics (Sections 9/14 of the project spec).

Two implementations are provided for every metric:

1. ``pytrec_eval``-backed (:func:`evaluate_run`) -- the trusted source of
   truth, wrapping the official ``trec_eval`` C implementation. This is what
   ``scripts/run_tfidf.py`` / ``scripts/run_bm25.py`` write to
   ``results/metrics/*.json``.
2. Custom from-scratch implementations (``precision_at_k``, ``recall_at_k``,
   ``reciprocal_rank``, ``average_precision``, ``ndcg_at_k`` and their
   ``mean_*`` aggregate wrappers) -- written for educational transparency and
   cross-checked against pytrec_eval in ``tests/test_metrics.py``. They are
   NOT used to produce the numbers reported in ``results/``; they exist to
   demonstrate (and unit-test) that the textbook formulas match what the
   trusted library actually computes.

Metrics produced: Precision@{1,5,10}, Recall@{10,20,50,100}, MRR, MRR@10,
MAP, MAP@100, nDCG@{5,10,20} -- per ``configs/default.yaml -> evaluation``.

Graded relevance (NFCorpus qrels are 0/1/2, not binary) -- INVESTIGATED, not
guessed, by directly probing ``pytrec_eval`` with a hand-built graded qrels
example (see the investigation reproduced in
``tests/test_metrics.py::TestGradedRelevanceHandling``):

  - Binary-style measures (P.k, recall.k, map, map_cut.k, recip_rank / MRR)
    treat ANY document with relevance > 0 as relevant, regardless of grade
    (1 and 2 are both "relevant"; only 0 is "not relevant"). This is
    trec_eval's built-in default behavior -- no manual threshold needs to be
    applied in this project's code, and none is.
  - P@k divides by k itself (not by the number of documents actually
    retrieved), so a query with fewer than k retrieved documents is
    penalized -- e.g. 3 relevant docs found within only 4 retrieved gives
    P@10 = 3/10, not 3/4. Verified empirically against pytrec_eval output.
  - nDCG (ndcg_cut.k) uses the GRADED relevance value itself as the gain --
    linear gain, gain(rel) = rel / log2(rank + 1) -- summed over ranks,
    NOT the exponential-gain variant gain(rel) = (2**rel - 1) that some
    other libraries (e.g. sklearn's ndcg_score) default to. Verified
    empirically: a graded example with relevance sequence [2, 1, 0, 1] in
    rank order gives ndcg_cut_10 = 0.97786 from pytrec_eval, matching the
    linear-gain formula (0.97786) and NOT the exponential-gain formula
    (0.98322).
  - A query with zero relevant documents in qrels evaluates to 0.0 for every
    measure (not NaN, not skipped) -- verified empirically.
  - pytrec_eval silently ignores any query present in the run but absent
    from qrels; :func:`evaluate_run` restricts to qrels' query IDs
    explicitly for the same reason, and documents queries dropped (if any).

Our custom implementations replicate all of the above exactly so they agree
with pytrec_eval within floating-point tolerance.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pytrec_eval

RunType = dict[str, list[tuple[str, float]]]
QrelsType = dict[str, dict[str, int]]

DEFAULT_PRECISION_CUTOFFS = (1, 5, 10)
DEFAULT_RECALL_CUTOFFS = (10, 20, 50, 100)
DEFAULT_NDCG_CUTOFFS = (5, 10, 20)
DEFAULT_MRR_CUTOFF = 10
DEFAULT_MAP_CUTOFF = 100


# ---------------------------------------------------------------------------
# pytrec_eval-backed evaluation (trusted / used for reported numbers)
# ---------------------------------------------------------------------------


def run_to_pytrec_format(run: RunType) -> dict[str, dict[str, float]]:
    """Convert ``{qid: [(docid, score), ...]}`` into pytrec_eval's expected shape."""
    return {qid: {docid: float(score) for docid, score in docs} for qid, docs in run.items()}


def evaluate_run(
    run: RunType,
    qrels: QrelsType,
    *,
    precision_cutoffs: tuple[int, ...] = DEFAULT_PRECISION_CUTOFFS,
    recall_cutoffs: tuple[int, ...] = DEFAULT_RECALL_CUTOFFS,
    ndcg_cutoffs: tuple[int, ...] = DEFAULT_NDCG_CUTOFFS,
    mrr_cutoff: int = DEFAULT_MRR_CUTOFF,
    map_cutoff: int = DEFAULT_MAP_CUTOFF,
    include_per_query: bool = False,
) -> dict[str, Any]:
    """Compute the full M2 metric set for ``run`` against ``qrels`` using pytrec_eval.

    ``run`` and ``qrels`` are keyed by query ID; ``run[qid]`` is a ranked list
    of ``(doc_id, score)`` tuples (highest score first is NOT required --
    pytrec_eval sorts by score itself). Queries present in ``run`` but absent
    from ``qrels`` are dropped (documented in ``dropped_queries``) since
    pytrec_eval has no relevance judgments to score them against.

    MRR@k is computed by truncating each ranked list to its top ``k``
    documents before invoking ``recip_rank`` -- pytrec_eval/trec_eval's
    ``recip_rank`` measure has no built-in cutoff, so a query's first
    relevant document beyond rank ``k`` must be hidden from it to get a
    genuine "MRR at 10" rather than "MRR over the full ranking".
    """
    qrels_query_ids = set(qrels.keys())
    run_query_ids = set(run.keys())
    dropped_queries = sorted(run_query_ids - qrels_query_ids)
    evaluated_query_ids = sorted(run_query_ids & qrels_query_ids)

    measures = set()
    for c in precision_cutoffs:
        measures.add(f"P.{c}")
    for c in recall_cutoffs:
        measures.add(f"recall.{c}")
    for c in ndcg_cutoffs:
        measures.add(f"ndcg_cut.{c}")
    measures.add("recip_rank")
    measures.add("map")
    measures.add(f"map_cut.{map_cutoff}")

    qrels_str = {qid: {did: int(rel) for did, rel in qrels[qid].items()} for qid in evaluated_query_ids}
    run_full = {qid: run_to_pytrec_format({qid: run[qid]})[qid] for qid in evaluated_query_ids}
    run_truncated_for_mrr = {
        qid: run_to_pytrec_format({qid: run[qid][:mrr_cutoff]})[qid] for qid in evaluated_query_ids
    }

    evaluator = pytrec_eval.RelevanceEvaluator(qrels_str, measures)
    per_query = evaluator.evaluate(run_full)

    mrr_evaluator = pytrec_eval.RelevanceEvaluator(qrels_str, {"recip_rank"})
    per_query_mrr_at_k = mrr_evaluator.evaluate(run_truncated_for_mrr)

    for qid in evaluated_query_ids:
        per_query.setdefault(qid, {})
        per_query[qid]["recip_rank_at_k"] = per_query_mrr_at_k.get(qid, {}).get("recip_rank", 0.0)

    n = len(evaluated_query_ids)
    summary: dict[str, float] = {}
    if n:
        for c in precision_cutoffs:
            summary[f"P@{c}"] = _mean(per_query[qid].get(f"P_{c}", 0.0) for qid in evaluated_query_ids)
        for c in recall_cutoffs:
            summary[f"Recall@{c}"] = _mean(
                per_query[qid].get(f"recall_{c}", 0.0) for qid in evaluated_query_ids
            )
        for c in ndcg_cutoffs:
            summary[f"nDCG@{c}"] = _mean(
                per_query[qid].get(f"ndcg_cut_{c}", 0.0) for qid in evaluated_query_ids
            )
        summary["MRR"] = _mean(per_query[qid].get("recip_rank", 0.0) for qid in evaluated_query_ids)
        summary[f"MRR@{mrr_cutoff}"] = _mean(
            per_query[qid].get("recip_rank_at_k", 0.0) for qid in evaluated_query_ids
        )
        summary["MAP"] = _mean(per_query[qid].get("map", 0.0) for qid in evaluated_query_ids)
        summary[f"MAP@{map_cutoff}"] = _mean(
            per_query[qid].get(f"map_cut_{map_cutoff}", 0.0) for qid in evaluated_query_ids
        )

    result: dict[str, Any] = {
        "num_queries_evaluated": n,
        "dropped_queries_not_in_qrels": dropped_queries,
        "summary": summary,
    }
    if include_per_query:
        result["per_query"] = per_query
    return result


def _mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


# ---------------------------------------------------------------------------
# TREC run I/O
# ---------------------------------------------------------------------------


def save_trec_run(run: RunType, path: str | Path, run_tag: str) -> Path:
    """Write ``run`` in standard TREC format: ``qid Q0 docid rank score run_tag``."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for qid, docs in run.items():
            for rank, (docid, score) in enumerate(docs, start=1):
                f.write(f"{qid} Q0 {docid} {rank} {score:.6f} {run_tag}\n")
    return path


def save_run_json(run: RunType, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump({qid: [[d, s] for d, s in docs] for qid, docs in run.items()}, f)
    return path


def load_trec_run(path: str | Path) -> RunType:
    """Parse a TREC-format run file back into ``{qid: [(docid, score), ...]}``."""
    run: dict[str, list[tuple[str, float]]] = {}
    with open(path) as f:
        for line in f:
            parts = line.split()
            if len(parts) < 6:
                continue
            qid, _q0, docid, _rank, score, _tag = parts[:6]
            run.setdefault(qid, []).append((docid, float(score)))
    for qid in run:
        run[qid].sort(key=lambda x: -x[1])
    return run


# ---------------------------------------------------------------------------
# Custom educational metric implementations (Section 14 of the spec)
# ---------------------------------------------------------------------------
#
# Each function scores ONE query's ranked list of doc IDs (highest-ranked
# first) against that query's relevance judgments {doc_id: relevance_grade}.
# Binary relevance for P/Recall/MRR/MAP is defined as relevance > 0, matching
# trec_eval's convention documented above.


def _is_relevant(rel: int) -> bool:
    return rel > 0


def precision_at_k(ranked_doc_ids: list[str], qrels: dict[str, int], k: int) -> float:
    """P@k = (# relevant docs in top k) / k (denominator is k, not len(retrieved))."""
    if k <= 0:
        raise ValueError("k must be positive")
    top_k = ranked_doc_ids[:k]
    num_relevant = sum(1 for d in top_k if _is_relevant(qrels.get(d, 0)))
    return num_relevant / k


def recall_at_k(ranked_doc_ids: list[str], qrels: dict[str, int], k: int) -> float:
    """Recall@k = (# relevant docs in top k) / (total # relevant docs in qrels)."""
    if k <= 0:
        raise ValueError("k must be positive")
    total_relevant = sum(1 for rel in qrels.values() if _is_relevant(rel))
    if total_relevant == 0:
        return 0.0
    top_k = ranked_doc_ids[:k]
    num_relevant = sum(1 for d in top_k if _is_relevant(qrels.get(d, 0)))
    return num_relevant / total_relevant


def reciprocal_rank(ranked_doc_ids: list[str], qrels: dict[str, int], k: int | None = None) -> float:
    """1 / (rank of first relevant doc), 0.0 if none found (within top k if given)."""
    candidates = ranked_doc_ids[:k] if k is not None else ranked_doc_ids
    for rank, d in enumerate(candidates, start=1):
        if _is_relevant(qrels.get(d, 0)):
            return 1.0 / rank
    return 0.0


def average_precision(ranked_doc_ids: list[str], qrels: dict[str, int], k: int | None = None) -> float:
    """Mean of precision@i evaluated at each rank i where a relevant doc appears.

    Averaged over the TOTAL number of relevant documents in qrels (not just
    the ones actually retrieved), matching trec_eval's ``map`` semantics --
    a relevant document never retrieved contributes a precision of 0 to the
    denominator's implicit count, not to the numerator's sum.
    """
    total_relevant = sum(1 for rel in qrels.values() if _is_relevant(rel))
    if total_relevant == 0:
        return 0.0
    candidates = ranked_doc_ids[:k] if k is not None else ranked_doc_ids
    hits = 0
    precisions_sum = 0.0
    for rank, d in enumerate(candidates, start=1):
        if _is_relevant(qrels.get(d, 0)):
            hits += 1
            precisions_sum += hits / rank
    return precisions_sum / total_relevant


def ndcg_at_k(ranked_doc_ids: list[str], qrels: dict[str, int], k: int) -> float:
    """nDCG@k with LINEAR gain (gain(rel) = rel), matching trec_eval's ndcg_cut.

    DCG@k = sum_{i=1}^{k} rel_i / log2(i + 1)   (1-indexed ranks)
    IDCG@k = DCG@k of the ideal ranking (relevance grades sorted descending)
    nDCG@k = DCG@k / IDCG@k  (0.0 if IDCG@k is 0, i.e. no relevant docs at all)
    """
    if k <= 0:
        raise ValueError("k must be positive")
    top_k = ranked_doc_ids[:k]
    gains = [qrels.get(d, 0) for d in top_k]
    dcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(gains))
    ideal_gains = sorted(qrels.values(), reverse=True)[:k]
    idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal_gains))
    return dcg / idcg if idcg > 0 else 0.0


def mean_precision_at_k(run: RunType, qrels: QrelsType, k: int) -> float:
    scores = [
        precision_at_k([d for d, _ in run[qid]], qrels[qid], k) for qid in run if qid in qrels
    ]
    return _mean(scores)


def mean_recall_at_k(run: RunType, qrels: QrelsType, k: int) -> float:
    scores = [recall_at_k([d for d, _ in run[qid]], qrels[qid], k) for qid in run if qid in qrels]
    return _mean(scores)


def mean_reciprocal_rank(run: RunType, qrels: QrelsType, k: int | None = None) -> float:
    scores = [
        reciprocal_rank([d for d, _ in run[qid]], qrels[qid], k) for qid in run if qid in qrels
    ]
    return _mean(scores)


def mean_average_precision(run: RunType, qrels: QrelsType, k: int | None = None) -> float:
    scores = [
        average_precision([d for d, _ in run[qid]], qrels[qid], k) for qid in run if qid in qrels
    ]
    return _mean(scores)


def mean_ndcg_at_k(run: RunType, qrels: QrelsType, k: int) -> float:
    scores = [ndcg_at_k([d for d, _ in run[qid]], qrels[qid], k) for qid in run if qid in qrels]
    return _mean(scores)
