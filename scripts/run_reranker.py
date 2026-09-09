#!/usr/bin/env python
"""M6: MedCPT cross-encoder reranking -- rerank the hybrid RRF (M5) run's
top candidates with ncbi/MedCPT-Cross-Encoder, evaluate against the real
test qrels, and write run/metrics/manifest artifacts.

Reuses results/runs/hybrid_rrf.trec (M5) as the candidate source rather
than re-running BM25/MedCPT/fusion. Sweeps candidate pool sizes
{20, 50, 100} (configs/reranker.yaml -> reranker.candidate_pool_sizes) in
one pass: the pool-50 result is written as the project's primary M6 result
(results/metrics/hybrid_reranked.json, matching
reranker.default_candidate_pool); all three pools' results are additionally
written to results/metrics/reranker_pool_ablation.json for ablation A6
(Section 18 of the project spec), so the sweep isn't thrown away after
picking a default.

Produces:
    results/runs/hybrid_reranked.trec, results/runs/hybrid_reranked.json  (pool=50)
    results/metrics/hybrid_reranked.json                                  (pool=50)
    results/metrics/reranker_pool_ablation.json                           (pools 20/50/100)
    results/manifests/exp-reranker-001.json

Usage:
    python scripts/run_reranker.py [--config configs/reranker.yaml]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from biomedical_ir.data import load_nfcorpus_from_raw  # noqa: E402
from biomedical_ir.evaluation import (  # noqa: E402
    evaluate_run,
    load_trec_run,
    save_run_json,
    save_trec_run,
)
from biomedical_ir.manifests import build_manifest, save_manifest  # noqa: E402
from biomedical_ir.reranker import CrossEncoderReranker, RerankerConfig  # noqa: E402
from biomedical_ir.utils import detect_device, ensure_dirs, load_config, set_seed  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/reranker.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    set_seed(cfg["seed"])

    ds_cfg = cfg["dataset"]
    paths = cfg["paths"]
    ensure_dirs(paths["runs_dir"], paths["metrics_dir"], paths["manifests_dir"])

    device = detect_device(cfg.get("device", {}).get("preference", "auto"))
    print(f"[run_reranker] device={device}")

    runs_dir = Path(paths["runs_dir"])
    hybrid_trec = runs_dir / "hybrid_rrf.trec"
    if not hybrid_trec.exists():
        print(
            f"[run_reranker] ERROR: {hybrid_trec} not found -- run scripts/run_hybrid.py first.",
            file=sys.stderr,
        )
        return 1

    print(f"[run_reranker] loading candidate run from {hybrid_trec}")
    hybrid_run = load_trec_run(hybrid_trec)
    print(f"[run_reranker] {len(hybrid_run)} queries with candidates")

    data = load_nfcorpus_from_raw(ds_cfg["raw_dir"])
    test_qrels = data.qrels.get("test", {})
    test_qids = sorted(test_qrels.keys())
    test_queries = {qid: data.queries[qid] for qid in test_qids if qid in data.queries}

    reranker_cfg_block = cfg.get("reranker", {})
    pool_sizes = reranker_cfg_block.get("candidate_pool_sizes", [20, 50, 100])
    default_pool = reranker_cfg_block.get("default_candidate_pool", 50)
    reranker_config = RerankerConfig.from_config(cfg)
    print(f"[run_reranker] config={reranker_config}, pool_sizes={pool_sizes}, default={default_pool}")

    load_start = time.perf_counter()
    reranker = CrossEncoderReranker(reranker_config, device=device)
    load_seconds = time.perf_counter() - load_start
    print(f"[run_reranker] cross-encoder loaded in {load_seconds:.3f}s")

    eval_cfg = cfg["evaluation"]
    ablation_results = {}
    default_run = None
    default_rerank_seconds = None

    for pool in pool_sizes:
        print(f"[run_reranker] reranking with candidate_pool={pool} ...")
        rerank_start = time.perf_counter()
        reranked_run = reranker.rerank_run(
            hybrid_run, test_queries, data.corpus, candidate_pool=pool, top_k=reranker_config.top_k
        )
        rerank_seconds = time.perf_counter() - rerank_start
        latency_ms_per_query = (rerank_seconds / len(reranked_run)) * 1000 if reranked_run else 0.0
        print(
            f"[run_reranker]   pool={pool}: reranked {len(reranked_run)} queries in "
            f"{rerank_seconds:.3f}s ({latency_ms_per_query:.3f} ms/query reranking-only)"
        )

        results = evaluate_run(
            reranked_run,
            test_qrels,
            precision_cutoffs=tuple(eval_cfg["cutoffs"]["precision"]),
            recall_cutoffs=tuple(eval_cfg["cutoffs"]["recall"]),
            ndcg_cutoffs=tuple(eval_cfg["cutoffs"]["ndcg"]),
            mrr_cutoff=eval_cfg["mrr_cutoff"],
            map_cutoff=eval_cfg["map_cutoff"],
        )
        ablation_results[str(pool)] = {
            "candidate_pool": pool,
            "num_queries_evaluated": results["num_queries_evaluated"],
            "metrics": results["summary"],
            "reranking_seconds": round(rerank_seconds, 4),
            "reranking_latency_ms_per_query": round(latency_ms_per_query, 4),
        }

        if pool == default_pool:
            default_run = reranked_run
            default_rerank_seconds = rerank_seconds

    if default_run is None:
        print(
            f"[run_reranker] ERROR: default_candidate_pool={default_pool} not in "
            f"candidate_pool_sizes={pool_sizes}",
            file=sys.stderr,
        )
        return 1

    run_tag = "hybrid_reranked"
    trec_path = save_trec_run(default_run, runs_dir / "hybrid_reranked.trec", run_tag)
    json_path = save_run_json(default_run, runs_dir / "hybrid_reranked.json")
    print(f"[run_reranker] wrote {trec_path} and {json_path} (pool={default_pool})")

    # Honest end-to-end latency for the default pool: hybrid RRF's own
    # end-to-end latency (bm25 + medcpt + fusion) plus this pool's reranking
    # time -- a real query pays the full pipeline's cost, not reranking alone.
    hybrid_metrics_path = Path(paths["metrics_dir"]) / "hybrid_rrf.json"
    hybrid_latency_ms = None
    if hybrid_metrics_path.exists():
        hybrid_payload = json.loads(hybrid_metrics_path.read_text())
        hybrid_latency_ms = hybrid_payload.get("timing", {}).get("latency_ms_per_query")

    default_latency_ms = ablation_results[str(default_pool)]["reranking_latency_ms_per_query"]
    end_to_end_latency_ms = (
        hybrid_latency_ms + default_latency_ms if hybrid_latency_ms is not None else None
    )

    metrics_payload = {
        "model": "hybrid_reranked",
        "config_path": args.config,
        "parameters": {"reranker": asdict(reranker_config), "candidate_pool": default_pool},
        "split": "test",
        "num_queries_evaluated": ablation_results[str(default_pool)]["num_queries_evaluated"],
        "metrics": ablation_results[str(default_pool)]["metrics"],
        "timing": {
            "model_load_seconds": round(load_seconds, 4),
            "reranking_seconds": round(default_rerank_seconds, 4),
            "reranking_latency_ms_per_query": default_latency_ms,
            "hybrid_rrf_latency_ms_per_query": hybrid_latency_ms,
            "latency_ms_per_query": round(end_to_end_latency_ms, 4)
            if end_to_end_latency_ms is not None
            else None,
            "latency_note": (
                "latency_ms_per_query = hybrid RRF's end-to-end latency (bm25 + medcpt + "
                "fusion) + this pool's reranking time, since a real query pays the full "
                "pipeline's cost, not reranking alone."
            ),
        },
        "device": device,
    }
    metrics_path = Path(paths["metrics_dir"]) / "hybrid_reranked.json"
    metrics_path.write_text(json.dumps(metrics_payload, indent=2))
    print(f"[run_reranker] wrote {metrics_path}")

    ablation_path = Path(paths["metrics_dir"]) / "reranker_pool_ablation.json"
    ablation_path.write_text(
        json.dumps(
            {
                "ablation": "A6 - candidate pool size sweep",
                "pool_sizes_tested": pool_sizes,
                "default_pool": default_pool,
                "results_by_pool": ablation_results,
            },
            indent=2,
        )
    )
    print(f"[run_reranker] wrote {ablation_path}")

    total_seconds = load_seconds + sum(
        ablation_results[str(p)]["reranking_seconds"] for p in pool_sizes
    )
    manifest = build_manifest(
        experiment_id="exp-reranker-001",
        dataset=ds_cfg["name"],
        split="test",
        model=reranker_config.model,
        parameters=metrics_payload["parameters"],
        seed=cfg["seed"],
        device=device,
        runtime_seconds=total_seconds,
        status="complete",
        extra={
            "num_queries_evaluated": metrics_payload["num_queries_evaluated"],
            "candidate_pool_sizes_tested": pool_sizes,
            "default_candidate_pool": default_pool,
        },
    )
    manifest_path = save_manifest(manifest, paths["manifests_dir"])
    print(f"[run_reranker] wrote {manifest_path}")

    print(
        "\n=== Hybrid + MedCPT Cross-Encoder Reranker (pool={}, test split, n={} queries) ===".format(
            default_pool, metrics_payload["num_queries_evaluated"]
        )
    )
    for k, v in metrics_payload["metrics"].items():
        print(f"  {k:12s} {v:.4f}")
    if end_to_end_latency_ms is not None:
        print(f"  {'Latency':12s} {end_to_end_latency_ms:.3f} ms/query (end-to-end)")

    print("\n=== Candidate pool ablation (A6) ===")
    for pool in pool_sizes:
        m = ablation_results[str(pool)]["metrics"]
        print(
            f"  pool={pool:>3}: nDCG@10={m['nDCG@10']:.4f} MAP={m['MAP']:.4f} "
            f"P@10={m['P@10']:.4f} reranking_latency="
            f"{ablation_results[str(pool)]['reranking_latency_ms_per_query']:.3f}ms/query"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
