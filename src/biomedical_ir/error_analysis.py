"""Automatic query-level diagnostic analysis (M8, Section 17 of the project spec).

For every (query, relevant document) pair in the test qrels, looks up that
document's rank in each of the six models' runs and classifies the pair
into one of six diagnostic categories:

    bm25_wins_medcpt_loses       -- BM25 ranks it well, MedCPT badly/misses it
    medcpt_wins_bm25_loses       -- the reverse
    hybrid_fixes_lexical_failure -- BM25 missed it, but Hybrid RRF ranks it well
    hybrid_fixes_semantic_failure-- MedCPT missed it, but Hybrid RRF ranks it well
    reranker_improves_result     -- reranking moves it to a meaningfully better rank
    reranker_degrades_result     -- reranking moves it to a meaningfully worse rank

"Wins/misses well/badly" are defined by two configurable rank thresholds
(GOOD_RANK, BAD_RANK) applied to each model's own top-100 run -- a document
absent from a run entirely (not in its top 100) counts as rank=None, treated
as "worse than BAD_RANK" for comparison purposes.

This module only DIAGNOSES from real run/qrels data; it never invents a
document, query, or rank that isn't actually present in
results/runs/*.json.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

RunType = dict[str, list[tuple[str, float]]]

GOOD_RANK = 10
BAD_RANK = 50


def get_rank(run: RunType, qid: str, doc_id: str) -> int | None:
    """1-indexed rank of doc_id in run[qid], or None if absent from that run."""
    doc_ids = [d for d, _ in run.get(qid, [])]
    if doc_id not in doc_ids:
        return None
    return doc_ids.index(doc_id) + 1


def _worse_than(rank: int | None, threshold: int) -> bool:
    """True if rank is None (never retrieved) or strictly worse than threshold."""
    return rank is None or rank > threshold


def _better_than(rank: int | None, threshold: int) -> bool:
    return rank is not None and rank <= threshold


@dataclass
class ErrorExample:
    category: str
    query_id: str
    query: str
    doc_id: str
    relevance: int
    doc_title: str
    doc_snippet: str
    ranks: dict[str, int | None]  # model -> rank (None if not retrieved)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _snippet(text: str, max_chars: int = 220) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "..."


def diagnose(
    runs: dict[str, RunType],
    queries: dict[str, str],
    qrels: dict[str, dict[str, int]],
    corpus: dict[str, dict[str, str]],
    *,
    max_examples_per_category: int = 5,
    good_rank: int = GOOD_RANK,
    bad_rank: int = BAD_RANK,
) -> dict[str, list[ErrorExample]]:
    """Classify every (query, relevant doc) pair into diagnostic categories.

    ``runs`` must contain keys "tfidf", "bm25", "bge", "medcpt",
    "hybrid_rrf", "hybrid_reranked" (a subset is fine; missing models are
    simply skipped for the categories that need them).
    """
    categories: dict[str, list[tuple[float, ErrorExample]]] = {
        "bm25_wins_medcpt_loses": [],
        "medcpt_wins_bm25_loses": [],
        "hybrid_fixes_lexical_failure": [],
        "hybrid_fixes_semantic_failure": [],
        "reranker_improves_result": [],
        "reranker_degrades_result": [],
    }

    for qid, doc_rels in qrels.items():
        if qid not in queries:
            continue
        for doc_id, rel in doc_rels.items():
            if rel <= 0 or doc_id not in corpus:
                continue  # only genuinely relevant, real documents are useful examples

            ranks = {
                model: get_rank(run, qid, doc_id)
                for model, run in runs.items()
            }
            bm25_r = ranks.get("bm25")
            medcpt_r = ranks.get("medcpt")
            hybrid_r = ranks.get("hybrid_rrf")
            reranked_r = ranks.get("hybrid_reranked")

            doc = corpus[doc_id]
            base_kwargs = dict(
                query_id=qid,
                query=queries[qid],
                doc_id=doc_id,
                relevance=rel,
                doc_title=doc.get("title", ""),
                doc_snippet=_snippet(doc.get("text", "")),
                ranks=ranks,
            )

            # BM25 wins / MedCPT loses -- and the reverse
            if _better_than(bm25_r, good_rank) and _worse_than(medcpt_r, bad_rank):
                gap = (medcpt_r or 999) - bm25_r
                categories["bm25_wins_medcpt_loses"].append(
                    (gap, ErrorExample(category="bm25_wins_medcpt_loses", **base_kwargs))
                )
            if _better_than(medcpt_r, good_rank) and _worse_than(bm25_r, bad_rank):
                gap = (bm25_r or 999) - medcpt_r
                categories["medcpt_wins_bm25_loses"].append(
                    (gap, ErrorExample(category="medcpt_wins_bm25_loses", **base_kwargs))
                )

            # Hybrid recovering from one component's failure
            if hybrid_r is not None:
                if _worse_than(bm25_r, bad_rank) and _better_than(hybrid_r, good_rank):
                    gap = (bm25_r or 999) - hybrid_r
                    categories["hybrid_fixes_lexical_failure"].append(
                        (gap, ErrorExample(category="hybrid_fixes_lexical_failure", **base_kwargs))
                    )
                if _worse_than(medcpt_r, bad_rank) and _better_than(hybrid_r, good_rank):
                    gap = (medcpt_r or 999) - hybrid_r
                    categories["hybrid_fixes_semantic_failure"].append(
                        (gap, ErrorExample(category="hybrid_fixes_semantic_failure", **base_kwargs))
                    )

            # Reranker's effect relative to the hybrid ranking it started from
            if hybrid_r is not None and reranked_r is not None:
                delta = hybrid_r - reranked_r  # positive = reranker improved the rank
                if delta > 0:
                    categories["reranker_improves_result"].append(
                        (delta, ErrorExample(category="reranker_improves_result", **base_kwargs))
                    )
                elif delta < 0:
                    categories["reranker_degrades_result"].append(
                        (-delta, ErrorExample(category="reranker_degrades_result", **base_kwargs))
                    )

    result: dict[str, list[ErrorExample]] = {}
    for category, scored in categories.items():
        scored.sort(key=lambda x: -x[0])
        result[category] = [ex for _, ex in scored[:max_examples_per_category]]
    return result


def diagnose_with_counts(
    runs: dict[str, RunType],
    queries: dict[str, str],
    qrels: dict[str, dict[str, int]],
    corpus: dict[str, dict[str, str]],
    *,
    max_examples_per_category: int = 5,
    good_rank: int = GOOD_RANK,
    bad_rank: int = BAD_RANK,
) -> tuple[dict[str, list[ErrorExample]], dict[str, int]]:
    """Like :func:`diagnose`, but also returns the TOTAL count found per
    category before truncation to ``max_examples_per_category`` -- useful
    for reporting "N examples found, showing top K" rather than silently
    implying only K examples exist."""
    full = diagnose(
        runs,
        queries,
        qrels,
        corpus,
        max_examples_per_category=10**9,  # effectively unlimited
        good_rank=good_rank,
        bad_rank=bad_rank,
    )
    counts = {category: len(examples) for category, examples in full.items()}
    truncated = {
        category: examples[:max_examples_per_category] for category, examples in full.items()
    }
    return truncated, counts
