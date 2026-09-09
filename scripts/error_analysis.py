#!/usr/bin/env python
"""M8: query-level error analysis -- classify (query, relevant document) pairs
from the real test qrels into six diagnostic categories (Section 17 of the
project spec) using the six real model runs from M2-M6, and write paper-ready
examples.

Produces:
    results/error-analysis/error_analysis.json
    results/error-analysis/error_analysis.md   (paper-ready, human-readable)
    results/manifests/exp-error-analysis-001.json

Usage:
    python scripts/error_analysis.py [--config configs/default.yaml] [--max-examples 5]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from biomedical_ir.data import load_nfcorpus_from_raw  # noqa: E402
from biomedical_ir.error_analysis import diagnose_with_counts  # noqa: E402
from biomedical_ir.evaluation import load_run_json  # noqa: E402
from biomedical_ir.manifests import build_manifest, save_manifest  # noqa: E402
from biomedical_ir.utils import ensure_dirs, load_config, set_seed  # noqa: E402

CATEGORY_TITLES = {
    "bm25_wins_medcpt_loses": "BM25 wins / MedCPT loses",
    "medcpt_wins_bm25_loses": "MedCPT wins / BM25 loses",
    "hybrid_fixes_lexical_failure": "Hybrid fixes a lexical (BM25) failure",
    "hybrid_fixes_semantic_failure": "Hybrid fixes a semantic (MedCPT) failure",
    "reranker_improves_result": "Reranker improves the result",
    "reranker_degrades_result": "Reranker degrades the result",
}

MODELS = ["tfidf", "bm25", "bge", "medcpt", "hybrid_rrf", "hybrid_reranked"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--max-examples", type=int, default=5)
    args = parser.parse_args()

    start = time.perf_counter()
    cfg = load_config(args.config)
    set_seed(cfg["seed"])

    ds_cfg = cfg["dataset"]
    paths = cfg["paths"]
    error_analysis_dir = Path(paths["error_analysis_dir"])
    ensure_dirs(error_analysis_dir, paths["manifests_dir"])

    runs_dir = Path(paths["runs_dir"])
    print("[error_analysis] loading all 6 model runs from results/runs/*.json ...")
    runs = {}
    for model in MODELS:
        run_path = runs_dir / f"{model}.json"
        if not run_path.exists():
            print(f"[error_analysis] ERROR: {run_path} not found.", file=sys.stderr)
            return 1
        runs[model] = load_run_json(run_path)

    data = load_nfcorpus_from_raw(ds_cfg["raw_dir"])
    test_qrels = data.qrels.get("test", {})
    print(f"[error_analysis] diagnosing {len(test_qrels)} test queries against {len(data.corpus)} docs ...")

    examples, counts = diagnose_with_counts(
        runs, data.queries, test_qrels, data.corpus, max_examples_per_category=args.max_examples
    )

    payload = {
        "description": "Query-level diagnostic examples (Section 17 of the project spec). "
        "Every example is drawn from real results/runs/*.json data against real qrels_test.json "
        "relevance judgments -- nothing here is synthesized.",
        "rank_thresholds": {"good_rank": 10, "bad_rank": 50},
        "total_examples_found_per_category": counts,
        "examples_shown_per_category": args.max_examples,
        "categories": {
            category: [ex.to_dict() for ex in ex_list] for category, ex_list in examples.items()
        },
    }
    json_path = error_analysis_dir / "error_analysis.json"
    json_path.write_text(json.dumps(payload, indent=2))
    print(f"[error_analysis] wrote {json_path}")

    md_lines = [
        "# Query-level error analysis",
        "",
        "> Every example below is drawn from real `results/runs/*.json` data "
        "against real `qrels_test.json` relevance judgments. Rank thresholds: "
        "good <= 10, bad = None (not retrieved in top 100) or > 50.",
        "",
    ]
    for category, ex_list in examples.items():
        total = counts[category]
        md_lines.append(f"## {CATEGORY_TITLES[category]} ({total} found, showing top {len(ex_list)})")
        md_lines.append("")
        if not ex_list:
            md_lines.append("_No examples found in this run._")
            md_lines.append("")
            continue
        for ex in ex_list:
            ranks_str = ", ".join(
                f"{m}={r if r is not None else '-'}" for m, r in ex.ranks.items()
            )
            md_lines.append(f"**Query `{ex.query_id}`:** {ex.query}")
            md_lines.append(f"- Relevant doc `{ex.doc_id}` (relevance={ex.relevance}): *{ex.doc_title}*")
            md_lines.append(f"  > {ex.doc_snippet}")
            md_lines.append(f"- Ranks: {ranks_str}")
            md_lines.append("")
    (error_analysis_dir / "error_analysis.md").write_text("\n".join(md_lines) + "\n")
    print(f"[error_analysis] wrote {error_analysis_dir / 'error_analysis.md'}")

    total_seconds = time.perf_counter() - start
    manifest = build_manifest(
        experiment_id="exp-error-analysis-001",
        dataset=ds_cfg["name"],
        split="test",
        model="error_analysis",
        parameters={"max_examples_per_category": args.max_examples, "rank_thresholds": payload["rank_thresholds"]},
        seed=cfg["seed"],
        device="cpu",
        runtime_seconds=total_seconds,
        status="complete",
        extra={"total_examples_found_per_category": counts},
    )
    manifest_path = save_manifest(manifest, paths["manifests_dir"])
    print(f"[error_analysis] wrote {manifest_path}")

    print("\n=== M8 summary: examples found per category ===")
    for category, count in counts.items():
        print(f"  {CATEGORY_TITLES[category]:45s} {count:4d} found")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
