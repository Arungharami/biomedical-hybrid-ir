#!/usr/bin/env python
"""M7: full cross-model evaluation -- paired statistical significance testing
and an effectiveness/efficiency summary table, built on the six real runs
produced by M2-M6.

Runs the five comparisons Section 16 of the project spec calls out by name:
BM25 vs BGE, BM25 vs MedCPT, BGE vs MedCPT, MedCPT vs Hybrid, Hybrid vs
Hybrid+Reranker -- for each of the five primary metrics (P@10, Recall@100,
MAP, MRR@10, nDCG@10), using the paired bootstrap test
(src/biomedical_ir/statistics.py). Every model's per-query scores are loaded
from results/runs/*.json (not *.trec) specifically so that BM25's 25
zero-result test queries participate in the pairing rather than silently
vanishing (see evaluation.load_run_json's docstring).

Produces:
    results/tables/statistical_tests.json
    results/tables/statistical_tests.md
    results/tables/efficiency.json
    results/tables/efficiency.md
    results/manifests/exp-evaluate-all-001.json

Usage:
    python scripts/evaluate_all.py [--config configs/default.yaml]
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
from biomedical_ir.efficiency import build_efficiency_table  # noqa: E402
from biomedical_ir.evaluation import evaluate_run, load_run_json  # noqa: E402
from biomedical_ir.manifests import build_manifest, save_manifest  # noqa: E402
from biomedical_ir.statistics import aligned_scores, paired_bootstrap_test  # noqa: E402
from biomedical_ir.utils import ensure_dirs, load_config, set_seed  # noqa: E402

# Raw pytrec_eval per-query keys for the five primary metrics this project
# reports (see evaluation.py's evaluate_run per_query output).
PRIMARY_METRICS = {
    "P@10": "P_10",
    "Recall@100": "recall_100",
    "MAP": "map",
    "MRR@10": "recip_rank_at_k",
    "nDCG@10": "ndcg_cut_10",
}

# The five comparisons Section 16 of the project spec names explicitly, plus
# TF-IDF vs BM25 (addresses H1 directly -- every M2 writeup promised this
# would be resolved here, and it costs nothing extra to include).
COMPARISONS = [
    ("tfidf", "bm25"),
    ("bm25", "bge"),
    ("bm25", "medcpt"),
    ("bge", "medcpt"),
    ("medcpt", "hybrid_rrf"),
    ("hybrid_rrf", "hybrid_reranked"),
]

MODEL_LABELS = {
    "tfidf": "TF-IDF",
    "bm25": "BM25",
    "bge": "BGE",
    "medcpt": "MedCPT",
    "hybrid_rrf": "Hybrid RRF",
    "hybrid_reranked": "Hybrid+Reranker",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--n-resamples", type=int, default=10000)
    args = parser.parse_args()

    start = time.perf_counter()
    cfg = load_config(args.config)
    set_seed(cfg["seed"])

    ds_cfg = cfg["dataset"]
    paths = cfg["paths"]
    ensure_dirs(paths["tables_dir"], paths["manifests_dir"])

    runs_dir = Path(paths["runs_dir"])
    metrics_dir = Path(paths["metrics_dir"])
    tables_dir = Path(paths["tables_dir"])

    data = load_nfcorpus_from_raw(ds_cfg["raw_dir"])
    test_qrels = data.qrels.get("test", {})

    print("[evaluate_all] loading all 6 model runs from results/runs/*.json ...")
    models = ["tfidf", "bm25", "bge", "medcpt", "hybrid_rrf", "hybrid_reranked"]
    per_query_by_model: dict[str, dict[str, dict]] = {}
    for model in models:
        run_path = runs_dir / f"{model}.json"
        if not run_path.exists():
            print(f"[evaluate_all] ERROR: {run_path} not found.", file=sys.stderr)
            return 1
        run = load_run_json(run_path)
        results = evaluate_run(run, test_qrels, include_per_query=True)
        per_query_by_model[model] = results["per_query"]
        print(f"[evaluate_all]   {model}: {len(run)} queries loaded, {results['num_queries_evaluated']} evaluated")

    print(f"[evaluate_all] running {len(COMPARISONS)} comparisons x {len(PRIMARY_METRICS)} metrics ...")
    comparisons_out = []
    for model_a, model_b in COMPARISONS:
        for metric_name, raw_key in PRIMARY_METRICS.items():
            per_query_a = {qid: v.get(raw_key, 0.0) for qid, v in per_query_by_model[model_a].items()}
            per_query_b = {qid: v.get(raw_key, 0.0) for qid, v in per_query_by_model[model_b].items()}
            qids, arr_a, arr_b = aligned_scores(per_query_a, per_query_b)
            result = paired_bootstrap_test(
                arr_a,
                arr_b,
                metric=metric_name,
                model_a=MODEL_LABELS[model_a],
                model_b=MODEL_LABELS[model_b],
                n_resamples=args.n_resamples,
                seed=cfg["seed"],
            )
            comparisons_out.append(result.to_dict())
            print(
                f"[evaluate_all]   {MODEL_LABELS[model_a]} vs {MODEL_LABELS[model_b]} "
                f"[{metric_name}]: diff={result.mean_diff:+.4f} "
                f"CI=[{result.ci_low:+.4f},{result.ci_high:+.4f}] p={result.p_value:.4f} "
                f"{'SIGNIFICANT' if result.significant_at_05 else 'not significant'} (n={result.n_queries})"
            )

    stats_payload = {
        "method": "paired_bootstrap",
        "n_resamples": args.n_resamples,
        "seed": cfg["seed"],
        "alpha": 0.05,
        "comparisons": comparisons_out,
    }
    stats_json_path = tables_dir / "statistical_tests.json"
    stats_json_path.write_text(json.dumps(stats_payload, indent=2))
    print(f"[evaluate_all] wrote {stats_json_path}")

    stats_md_lines = [
        "# Statistical significance tests (paired bootstrap, n_resamples="
        f"{args.n_resamples}, seed={cfg['seed']})",
        "",
        "> Comparisons named in Section 16 of the project spec. Query-level "
        "paired bootstrap over the primary metrics; p < 0.05 flagged SIGNIFICANT. "
        "No comparison here should be read as proving a hypothesis outside the "
        "metric/comparison it specifically tests.",
        "",
        "| Comparison | Metric | A mean | B mean | Diff (A-B) | 95% CI | p-value | Significant | n |",
        "|---|---|---:|---:|---:|---|---:|:---:|---:|",
    ]
    for c in comparisons_out:
        sig = "**yes**" if c["significant_at_alpha_0.05"] else "no"
        stats_md_lines.append(
            f"| {c['model_a']} vs {c['model_b']} | {c['metric']} | {c['mean_a']:.4f} | "
            f"{c['mean_b']:.4f} | {c['mean_diff']:+.4f} | "
            f"[{c['ci_95_low']:+.4f}, {c['ci_95_high']:+.4f}] | {c['p_value']:.4f} | {sig} | {c['n_queries']} |"
        )
    (tables_dir / "statistical_tests.md").write_text("\n".join(stats_md_lines) + "\n")
    print(f"[evaluate_all] wrote {tables_dir / 'statistical_tests.md'}")

    print("[evaluate_all] building efficiency table ...")
    efficiency_rows = build_efficiency_table(metrics_dir)
    (tables_dir / "efficiency.json").write_text(json.dumps(efficiency_rows, indent=2))
    eff_md_lines = [
        "# Effectiveness / efficiency summary",
        "",
        "| Model | Device | Embedding dim | Index size (KB) | Latency (ms/query) | nDCG@10 | MAP | Recall@100 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in efficiency_rows:
        if r["status"] != "complete":
            continue
        dim = r["embedding_dim"] if r["embedding_dim"] is not None else "-"
        size_kb = f"{r['index_size_bytes'] / 1024:.1f}" if r["index_size_bytes"] else "-"
        lat = f"{r['latency_ms_per_query']:.3f}" if r["latency_ms_per_query"] is not None else "-"
        eff_md_lines.append(
            f"| {MODEL_LABELS.get(r['model'], r['model'])} | {r['device']} | {dim} | {size_kb} | "
            f"{lat} | {r['nDCG@10']:.4f} | {r['MAP']:.4f} | {r['Recall@100']:.4f} |"
        )
    (tables_dir / "efficiency.md").write_text("\n".join(eff_md_lines) + "\n")
    print(f"[evaluate_all] wrote {tables_dir / 'efficiency.json'} and {tables_dir / 'efficiency.md'}")

    total_seconds = time.perf_counter() - start
    n_significant = sum(1 for c in comparisons_out if c["significant_at_alpha_0.05"])
    manifest = build_manifest(
        experiment_id="exp-evaluate-all-001",
        dataset=ds_cfg["name"],
        split="test",
        model="statistical_analysis",
        parameters={
            "method": "paired_bootstrap",
            "n_resamples": args.n_resamples,
            "comparisons": COMPARISONS,
            "metrics": list(PRIMARY_METRICS.keys()),
        },
        seed=cfg["seed"],
        device="cpu",
        runtime_seconds=total_seconds,
        status="complete",
        extra={
            "n_comparisons_run": len(comparisons_out),
            "n_significant_at_0.05": n_significant,
        },
    )
    manifest_path = save_manifest(manifest, paths["manifests_dir"])
    print(f"[evaluate_all] wrote {manifest_path}")

    print(f"\n=== M7 summary: {n_significant}/{len(comparisons_out)} comparisons significant at alpha=0.05 ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
