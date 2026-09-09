#!/usr/bin/env python
"""M4: MedCPT biomedical dense retrieval -- encode the full NFCorpus corpus
(as title/text pairs, via ncbi/MedCPT-Article-Encoder) and the test-split
queries (via ncbi/MedCPT-Query-Encoder), index with FAISS (IndexFlatIP over
un-normalized embeddings, per the model cards), retrieve top-k, evaluate
against the real test qrels, and write run/metrics/manifest artifacts.

Produces:
    results/runs/medcpt.trec, results/runs/medcpt.json
    results/metrics/medcpt.json
    results/manifests/exp-medcpt-001.json

Usage:
    python scripts/run_medcpt.py [--config configs/medcpt.yaml]
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
from biomedical_ir.evaluation import evaluate_run, save_run_json, save_trec_run  # noqa: E402
from biomedical_ir.manifests import build_manifest, save_manifest  # noqa: E402
from biomedical_ir.medcpt import MedCPTConfig, MedCPTRetriever  # noqa: E402
from biomedical_ir.utils import detect_device, ensure_dirs, load_config, set_seed  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/medcpt.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    set_seed(cfg["seed"])

    ds_cfg = cfg["dataset"]
    paths = cfg["paths"]
    ensure_dirs(paths["runs_dir"], paths["metrics_dir"], paths["manifests_dir"])

    device = detect_device(cfg.get("device", {}).get("preference", "auto"))
    print(f"[run_medcpt] device={device}")

    print("[run_medcpt] loading NFCorpus from raw cache (no network) ...")
    data = load_nfcorpus_from_raw(ds_cfg["raw_dir"])
    print(f"[run_medcpt] corpus={len(data.corpus)} docs, queries={len(data.queries)}")

    test_qrels = data.qrels.get("test", {})
    test_qids = sorted(test_qrels.keys())
    test_queries = {qid: data.queries[qid] for qid in test_qids if qid in data.queries}
    print(f"[run_medcpt] test split: {len(test_queries)} queries with qrels")

    # MedCPT's article encoder consumes title/text as a structured pair
    # (see docs/models.md), not a pre-composed string -- data.corpus is
    # passed through directly rather than via compose_document_text.

    medcpt_config = MedCPTConfig.from_config(cfg)
    print(f"[run_medcpt] config={medcpt_config}")

    load_start = time.perf_counter()
    retriever = MedCPTRetriever(medcpt_config, device=device)
    load_seconds = time.perf_counter() - load_start
    print(f"[run_medcpt] both encoders loaded in {load_seconds:.3f}s")

    encode_start = time.perf_counter()
    doc_embeddings = retriever.build_index(data.corpus)
    encode_seconds = time.perf_counter() - encode_start
    embedding_dim = doc_embeddings.shape[1]
    index_size_bytes = retriever.index.index_size_bytes()
    print(
        f"[run_medcpt] encoded+indexed {len(data.corpus)} docs in {encode_seconds:.3f}s "
        f"(dim={embedding_dim}, index_size={index_size_bytes / 1024:.1f} KB)"
    )

    retrieve_start = time.perf_counter()
    run = retriever.rank_all(test_queries, top_k=medcpt_config.top_k)
    retrieve_seconds = time.perf_counter() - retrieve_start
    latency_ms_per_query = (retrieve_seconds / len(test_queries)) * 1000 if test_queries else 0.0
    print(
        f"[run_medcpt] retrieved top-{medcpt_config.top_k} for {len(run)} queries in "
        f"{retrieve_seconds:.3f}s ({latency_ms_per_query:.3f} ms/query, query encoding included)"
    )

    run_tag = "medcpt"
    trec_path = save_trec_run(run, Path(paths["runs_dir"]) / "medcpt.trec", run_tag)
    json_path = save_run_json(run, Path(paths["runs_dir"]) / "medcpt.json")
    print(f"[run_medcpt] wrote {trec_path} and {json_path}")

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
    total_seconds = load_seconds + encode_seconds + retrieve_seconds

    metrics_payload = {
        "model": "medcpt",
        "config_path": args.config,
        "parameters": {"model": asdict(medcpt_config)},
        "split": "test",
        "num_queries_evaluated": results["num_queries_evaluated"],
        "dropped_queries_not_in_qrels": results["dropped_queries_not_in_qrels"],
        "metrics": results["summary"],
        "timing": {
            "model_load_seconds": round(load_seconds, 4),
            "corpus_encoding_seconds": round(encode_seconds, 4),
            "retrieve_seconds": round(retrieve_seconds, 4),
            "total_seconds": round(total_seconds, 4),
            "latency_ms_per_query": round(latency_ms_per_query, 4),
        },
        "index": {
            "type": "IndexFlatIP",
            "embedding_dim": embedding_dim,
            "num_vectors": len(data.corpus),
            "size_bytes": index_size_bytes,
        },
        "device": device,
    }
    metrics_path = Path(paths["metrics_dir"]) / "medcpt.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics_payload, indent=2))
    print(f"[run_medcpt] wrote {metrics_path}")

    manifest = build_manifest(
        experiment_id="exp-medcpt-001",
        dataset=ds_cfg["name"],
        split="test",
        model=f"{medcpt_config.query_encoder} + {medcpt_config.article_encoder}",
        parameters=metrics_payload["parameters"],
        seed=cfg["seed"],
        device=device,
        runtime_seconds=total_seconds,
        status="complete",
        extra={
            "num_queries_evaluated": results["num_queries_evaluated"],
            "top_k": medcpt_config.top_k,
            "embedding_dim": embedding_dim,
            "index_size_bytes": index_size_bytes,
        },
    )
    manifest_path = save_manifest(manifest, paths["manifests_dir"])
    print(f"[run_medcpt] wrote {manifest_path}")

    print("\n=== MedCPT (test split, n={} queries) ===".format(results["num_queries_evaluated"]))
    for k, v in results["summary"].items():
        print(f"  {k:12s} {v:.4f}")
    print(f"  {'Latency':12s} {latency_ms_per_query:.3f} ms/query")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
