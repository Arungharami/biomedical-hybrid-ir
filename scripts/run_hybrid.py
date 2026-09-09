#!/usr/bin/env python
"""M5: Hybrid retrieval -- fuse the already-computed BM25 (M2) and MedCPT (M4)
test-split runs via Reciprocal Rank Fusion, evaluate against the real test
qrels, and write run/metrics/manifest artifacts.

Reuses results/runs/{bm25,medcpt}.trec rather than re-running either
retriever -- both already cover the same top-100 candidates for the same
323 test queries, which is exactly what RRF needs as input. Run
scripts/run_bm25.py and scripts/run_medcpt.py first if those artifacts are
missing or stale.

Produces:
    results/runs/hybrid_rrf.trec, results/runs/hybrid_rrf.json
    results/metrics/hybrid_rrf.json
    results/manifests/exp-hybrid-rrf-001.json

Usage:
    python scripts/run_hybrid.py [--config configs/hybrid.yaml]
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
from biomedical_ir.fusion import RRFConfig, fuse_runs  # noqa: E402
from biomedical_ir.manifests import build_manifest, save_manifest  # noqa: E402
from biomedical_ir.utils import ensure_dirs, load_config, set_seed  # noqa: E402


def _component_latency_ms(metrics_path: Path) -> float | None:
    if not metrics_path.exists():
        return None
    payload = json.loads(metrics_path.read_text())
    return payload.get("timing", {}).get("latency_ms_per_query")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/hybrid.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    set_seed(cfg["seed"])

    ds_cfg = cfg["dataset"]
    paths = cfg["paths"]
    ensure_dirs(paths["runs_dir"], paths["metrics_dir"], paths["manifests_dir"])

    runs_dir = Path(paths["runs_dir"])
    metrics_dir = Path(paths["metrics_dir"])
    bm25_trec = runs_dir / "bm25.trec"
    medcpt_trec = runs_dir / "medcpt.trec"
    for p in (bm25_trec, medcpt_trec):
        if not p.exists():
            print(
                f"[run_hybrid] ERROR: {p} not found -- run scripts/run_bm25.py and "
                "scripts/run_medcpt.py first.",
                file=sys.stderr,
            )
            return 1

    print(f"[run_hybrid] loading component runs from {bm25_trec} and {medcpt_trec}")
    bm25_run = load_trec_run(bm25_trec)
    medcpt_run = load_trec_run(medcpt_trec)
    print(f"[run_hybrid] bm25: {len(bm25_run)} queries, medcpt: {len(medcpt_run)} queries")

    data = load_nfcorpus_from_raw(ds_cfg["raw_dir"])
    test_qrels = data.qrels.get("test", {})

    rrf_config = RRFConfig.from_config(cfg)
    fusion_cfg_block = cfg.get("fusion", {})
    if fusion_cfg_block.get("tuning", {}).get("enabled", False):
        print(
            "[run_hybrid] WARNING: fusion.tuning.enabled=true in config, but this "
            "milestone (M5) does not implement dev-split k tuning; using the "
            "frozen default k as-is.",
            file=sys.stderr,
        )
    print(f"[run_hybrid] RRF config: {rrf_config}")

    fuse_start = time.perf_counter()
    run = fuse_runs(
        [bm25_run, medcpt_run],
        k=rrf_config.k,
        candidate_depth=rrf_config.candidate_depth,
        top_k=rrf_config.top_k,
    )
    fuse_seconds = time.perf_counter() - fuse_start
    fusion_latency_ms_per_query = (fuse_seconds / len(run)) * 1000 if run else 0.0
    print(f"[run_hybrid] fused {len(run)} queries in {fuse_seconds:.4f}s (fusion only)")

    # Honest end-to-end latency: a real hybrid query pays BOTH component
    # retrievers' cost PLUS fusion -- not just the (near-instant) fusion step
    # itself. Pulled from each component's own recorded per-query latency
    # (results/metrics/{bm25,medcpt}.json) rather than re-measured here.
    bm25_latency = _component_latency_ms(metrics_dir / "bm25.json")
    medcpt_latency = _component_latency_ms(metrics_dir / "medcpt.json")
    end_to_end_latency_ms = None
    if bm25_latency is not None and medcpt_latency is not None:
        end_to_end_latency_ms = bm25_latency + medcpt_latency + fusion_latency_ms_per_query
        print(
            f"[run_hybrid] end-to-end latency estimate = bm25 ({bm25_latency:.3f}ms) + "
            f"medcpt ({medcpt_latency:.3f}ms) + fusion ({fusion_latency_ms_per_query:.4f}ms) "
            f"= {end_to_end_latency_ms:.3f} ms/query"
        )
    else:
        print(
            "[run_hybrid] WARNING: results/metrics/{bm25,medcpt}.json not found -- cannot "
            "compute end-to-end latency estimate; only fusion-only latency will be reported.",
            file=sys.stderr,
        )

    run_tag = "hybrid_rrf"
    trec_path = save_trec_run(run, runs_dir / "hybrid_rrf.trec", run_tag)
    json_path = save_run_json(run, runs_dir / "hybrid_rrf.json")
    print(f"[run_hybrid] wrote {trec_path} and {json_path}")

    eval_cfg = cfg["evaluation"]
    results = evaluate_run(
        run,
        test_qrels,
        precision_cutoffs=tuple(eval_cfg["cutoffs"]["precision"]),
        recall_cutoffs=tuple(eval_cfg["cutoffs"]["recall"]),
        ndcg_cutoffs=tuple(eval_cfg["cutoffs"]["ndcg"]),
        mrr_cutoff=eval_cfg["mrr_cutoff"],
        map_cutoff=eval_cfg["map_cutoff"],
    )

    metrics_payload = {
        "model": "hybrid_rrf",
        "config_path": args.config,
        "parameters": {"fusion": asdict(rrf_config), "components": ["bm25", "medcpt"]},
        "split": "test",
        "num_queries_evaluated": results["num_queries_evaluated"],
        "dropped_queries_not_in_qrels": results["dropped_queries_not_in_qrels"],
        "metrics": results["summary"],
        "timing": {
            "fusion_seconds": round(fuse_seconds, 6),
            "fusion_latency_ms_per_query": round(fusion_latency_ms_per_query, 4),
            "component_bm25_latency_ms_per_query": bm25_latency,
            "component_medcpt_latency_ms_per_query": medcpt_latency,
            "latency_ms_per_query": round(end_to_end_latency_ms, 4)
            if end_to_end_latency_ms is not None
            else None,
            "latency_note": (
                "latency_ms_per_query = bm25 retrieval + medcpt retrieval + RRF fusion, "
                "since a real hybrid query pays both component retrievers' cost."
            ),
        },
    }
    metrics_path = metrics_dir / "hybrid_rrf.json"
    metrics_path.write_text(json.dumps(metrics_payload, indent=2))
    print(f"[run_hybrid] wrote {metrics_path}")

    manifest = build_manifest(
        experiment_id="exp-hybrid-rrf-001",
        dataset=ds_cfg["name"],
        split="test",
        model="bm25+medcpt-rrf",
        parameters=metrics_payload["parameters"],
        seed=cfg["seed"],
        device="cpu",  # fusion itself is pure CPU rank arithmetic
        runtime_seconds=fuse_seconds,
        status="complete",
        extra={
            "num_queries_evaluated": results["num_queries_evaluated"],
            "top_k": rrf_config.top_k,
            "note": "Fuses precomputed results/runs/{bm25,medcpt}.trec; see docs for provenance.",
        },
    )
    manifest_path = save_manifest(manifest, paths["manifests_dir"])
    print(f"[run_hybrid] wrote {manifest_path}")

    print("\n=== Hybrid BM25+MedCPT RRF (test split, n={} queries) ===".format(
        results["num_queries_evaluated"]
    ))
    for k, v in results["summary"].items():
        print(f"  {k:12s} {v:.4f}")
    if end_to_end_latency_ms is not None:
        print(f"  {'Latency':12s} {end_to_end_latency_ms:.3f} ms/query (end-to-end)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
