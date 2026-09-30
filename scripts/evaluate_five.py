#!/usr/bin/env python3
"""Course-specific evaluation of five judged NFCorpus test queries.

Uses ALL official qrels for each selected query, not just the single
illustrative relevant document listed in docs/cap6776-final-plan.md.
Runs the existing pytrec_eval-backed evaluation against stored real rankings.
"""
from __future__ import annotations

from pathlib import Path

from biomedical_ir.data import load_nfcorpus_from_raw
from biomedical_ir.evaluation import evaluate_run, load_run_json

QUERY_IDS = [
    "PLAIN-2040",  # salmon
    "PLAIN-12",    # Exploiting Autophagy to Live Longer
    "PLAIN-817",   # canker sores
    "PLAIN-1214",  # Fosamax
    "PLAIN-33",    # What's Driving America's Obesity Problem?
]
MODELS = ["tfidf", "bm25", "bge", "medcpt", "hybrid_rrf", "hybrid_reranked"]


def main():
    ds = load_nfcorpus_from_raw("data/raw/nfcorpus")
    qrels = {qid: ds.qrels["test"][qid] for qid in QUERY_IDS}
    print("Five-query evaluation (official NFCorpus test qrels, all judgments per query)")
    for qid in QUERY_IDS:
        positive = sum(1 for grade in qrels[qid].values() if grade > 0)
        print(f"  {qid}: {ds.queries[qid]} | judged relevant documents: {positive}")

    print()
    for name in MODELS:
        path = Path("results/runs") / f"{name}.json"
        if not path.exists():
            print(f"{name}: SKIPPED (missing {path})")
            continue
        full_run = load_run_json(path)
        selected_run = {qid: full_run.get(qid, []) for qid in QUERY_IDS}
        result = evaluate_run(selected_run, qrels, include_per_query=True)
        print(f"{name}: mean P@10={result['summary']['P@10']:.4f} "
              f"mean nDCG@10={result['summary']['nDCG@10']:.4f}")
        for qid in QUERY_IDS:
            per = result["per_query"].get(qid, {})
            print(f"    {qid:12s} P@10={per.get('P_10', 0.0):.4f} "
                  f"nDCG@10={per.get('ndcg_cut_10', 0.0):.4f}")


if __name__ == "__main__":
    main()
