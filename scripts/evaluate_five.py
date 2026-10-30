#!/usr/bin/env python3
"""CAP 6776 requirement: >=5 queries with relevance judgments + a standard metric.

Scores the six recorded model runs (results/runs/*.json, all 323 test queries)
on five hand-picked NFCorpus test queries using ALL official graded test qrels
for each query. Metrics: P@10, nDCG@10, RR@10 (MRR@10 when averaged).

Primary numbers come from pytrec_eval (the project's trusted evaluator). The
project's own from-scratch metric functions are run alongside as a
cross-check; the script fails loudly if the two disagree.

    python scripts/evaluate_five.py
    -> prints tables, writes results/tables/five_query_eval.{md,json}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from biomedical_ir.data import load_nfcorpus_from_raw  # noqa: E402
from biomedical_ir.evaluation import (  # noqa: E402
    evaluate_run,
    load_run_json,
    ndcg_at_k,
    precision_at_k,
    reciprocal_rank,
)

# Chosen to span the behaviours discussed in the presentation:
QUERY_IDS = [
    "PLAIN-2040",  # "salmon"                - exact keyword; lexical should do well
    "PLAIN-12",    # autophagy / longevity   - conceptual phrasing
    "PLAIN-817",   # "canker sores"          - lay term vs. medical vocabulary
    "PLAIN-1214",  # "Fosamax"               - brand name; BM25 returns NOTHING (no shared term)
    "PLAIN-33",    # obesity question        - long natural-language question
]
MODELS = [
    ("tfidf", "TF-IDF"),
    ("bm25", "BM25"),
    ("bge", "BGE (general dense)"),
    ("medcpt", "MedCPT (biomedical dense)"),
    ("hybrid_rrf", "Hybrid BM25+MedCPT (RRF)"),
    ("hybrid_reranked", "Hybrid + cross-encoder"),
]
OUT_DIR = ROOT / "results" / "tables"


def main() -> None:
    ds = load_nfcorpus_from_raw(ROOT / "data" / "raw" / "nfcorpus")
    test_qrels = ds.qrels["test"]
    missing = [q for q in QUERY_IDS if q not in test_qrels]
    if missing:
        raise SystemExit(f"Not in official test qrels: {missing}")
    qrels = {q: test_qrels[q] for q in QUERY_IDS}

    query_rows = []
    for q in QUERY_IDS:
        grades = list(qrels[q].values())
        query_rows.append({
            "qid": q,
            "query": ds.queries[q],
            "relevant": sum(g > 0 for g in grades),
            "grade2": sum(g == 2 for g in grades),
        })

    try:
        import pytrec_eval  # noqa: F401

        have_pytrec = True
    except ImportError:
        have_pytrec = False
        print("WARNING: pytrec_eval not installed - using the project's own metric functions only.")

    results = {}
    for key, label in MODELS:
        path = ROOT / "results" / "runs" / f"{key}.json"
        if not path.exists():
            print(f"SKIP {label}: {path} missing")
            continue
        run = load_run_json(path)
        sel = {q: sorted(run.get(q, []), key=lambda x: (-x[1], x[0])) for q in QUERY_IDS}
        per = {}
        for q in QUERY_IDS:
            ids = [d for d, _ in sel[q]]
            per[q] = {
                "P@10": precision_at_k(ids, qrels[q], 10),
                "nDCG@10": ndcg_at_k(ids, qrels[q], 10),
                "RR@10": reciprocal_rank(ids, qrels[q], 10),
                "retrieved": len(ids),
                "relevant_in_top10": sum(qrels[q].get(d, 0) > 0 for d in ids[:10]),
            }
        if have_pytrec:
            # trec_eval re-sorts by score and breaks ties by doc id; RRF produces
            # many exact ties, so hand it strictly decreasing rank-based scores
            # to evaluate exactly the stored order.
            by_rank = {q: [(d, float(len(v) - i)) for i, (d, _) in enumerate(v)] for q, v in sel.items()}
            trusted = evaluate_run(by_rank, qrels, include_per_query=True)["per_query"]
            for q in QUERY_IDS:
                t = trusted[q]
                for ours, theirs in (("P@10", "P_10"), ("nDCG@10", "ndcg_cut_10"),
                                     ("RR@10", "recip_rank_at_k")):
                    if abs(per[q][ours] - t[theirs]) > 1e-6:
                        raise SystemExit(
                            f"Metric mismatch {label} {q} {ours}: ours={per[q][ours]} pytrec={t[theirs]}"
                        )
        mean = {m: sum(per[q][m] for q in QUERY_IDS) / len(QUERY_IDS) for m in ("P@10", "nDCG@10", "RR@10")}
        results[key] = {"label": label, "per_query": per, "mean": mean}

    md = render_markdown(query_rows, results, have_pytrec)
    print(md)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "five_query_eval.md").write_text(md)
    (OUT_DIR / "five_query_eval.json").write_text(
        json.dumps({"queries": query_rows, "results": results,
                    "cross_checked_with_pytrec_eval": have_pytrec}, indent=2)
    )
    print(f"\nWrote {OUT_DIR / 'five_query_eval.md'} and .json")


def render_markdown(query_rows, results, have_pytrec) -> str:
    lines = ["# Five judged queries (NFCorpus test qrels, all judgments per query)", ""]
    lines += ["| Query ID | Query | # judged relevant | # graded 2 |", "|---|---|---:|---:|"]
    for r in query_rows:
        lines.append(f"| {r['qid']} | {r['query']} | {r['relevant']} | {r['grade2']} |")
    lines += ["", "## Mean over the five queries", "",
              "| Model | P@10 | nDCG@10 | MRR@10 |", "|---|---:|---:|---:|"]
    for v in results.values():
        m = v["mean"]
        lines.append(f"| {v['label']} | {m['P@10']:.3f} | {m['nDCG@10']:.3f} | {m['RR@10']:.3f} |")
    lines += ["", "## Per query - nDCG@10 (relevant docs in top 10 in brackets)", ""]
    lines.append("| Model | " + " | ".join(r["qid"] for r in query_rows) + " |")
    lines.append("|---|" + "---:|" * len(query_rows))
    for v in results.values():
        cells = [
            f"{v['per_query'][r['qid']]['nDCG@10']:.3f} [{v['per_query'][r['qid']]['relevant_in_top10']}]"
            for r in query_rows
        ]
        lines.append(f"| {v['label']} | " + " | ".join(cells) + " |")
    lines += ["", "Cross-checked against pytrec_eval: " + ("yes, exact agreement" if have_pytrec else "NO")]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
