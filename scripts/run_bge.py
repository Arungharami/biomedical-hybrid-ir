#!/usr/bin/env python
"""M3: BGE general-purpose dense retrieval -- encode the full NFCorpus corpus
and the test-split queries with BAAI/bge-base-en-v1.5, index with FAISS
(IndexFlatIP over normalized embeddings), retrieve top-k, evaluate against
the real test qrels, and write run/metrics/manifest artifacts.

Produces:
    results/runs/bge.trec, results/runs/bge.json
    results/metrics/bge.json
    results/manifests/exp-bge-001.json

Usage:
    python scripts/run_bge.py [--config configs/bge.yaml]
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

from biomedical_ir.data import compose_document_text, load_nfcorpus_from_raw  # noqa: E402
from biomedical_ir.dense import DenseModelConfig, DenseRetriever  # noqa: E402
from biomedical_ir.evaluation import evaluate_run, save_run_json, save_trec_run  # noqa: E402
from biomedical_ir.manifests import build_manifest, save_manifest  # noqa: E402
from biomedical_ir.utils import detect_device, ensure_dirs, load_config, set_seed  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/bge.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    set_seed(cfg["seed"])

    ds_cfg = cfg["dataset"]
    paths = cfg["paths"]
    doc_comp = cfg["document_composition"]
    ensure_dirs(paths["runs_dir"], paths["metrics_dir"], paths["manifests_dir"])

    device = detect_device(cfg.get("device", {}).get("preference", "auto"))
    print(f"[run_bge] device={device}")

    print("[run_bge] loading NFCorpus from raw cache (no network) ...")
    data = load_nfcorpus_from_raw(ds_cfg["raw_dir"])
    print(f"[run_bge] corpus={len(data.corpus)} docs, queries={len(data.queries)}")

    test_qrels = data.qrels.get("test", {})
    test_qids = sorted(test_qrels.keys())
    test_queries = {qid: data.queries[qid] for qid in test_qids if qid in data.queries}
    print(f"[run_bge] test split: {len(test_queries)} queries with qrels")

    corpus_text = {
        doc_id: compose_document_text(
            d.get("title", ""), d.get("text", ""), doc_comp["strategy"], doc_comp["separator"]
        )
        for doc_id, d in data.corpus.items()
    }

    dense_config = DenseModelConfig.from_config(cfg)
    print(f"[run_bge] model={dense_config.name} config={dense_config}")

    load_start = time.perf_counter()
    retriever = DenseRetriever(dense_config, device=device)
    load_seconds = time.perf_counter() - load_start
    print(f"[run_bge] model loaded in {load_seconds:.3f}s")

    encode_start = time.perf_counter()
    doc_embeddings = retriever.build_index(corpus_text)
    encode_seconds = time.perf_counter() - encode_start
    embedding_dim = doc_embeddings.shape[1]
    index_size_bytes = retriever.index.index_size_bytes()
    print(
        f"[run_bge] encoded+indexed {len(corpus_text)} docs in {encode_seconds:.3f}s "
        f"(dim={embedding_dim}, index_size={index_size_bytes / 1024:.1f} KB)"
    )

    retrieve_start = time.perf_counter()
    run = retriever.rank_all(test_queries, top_k=dense_config.top_k)
    retrieve_seconds = time.perf_counter() - retrieve_start
    latency_ms_per_query = (retrieve_seconds / len(test_queries)) * 1000 if test_queries else 0.0
    print(
        f"[run_bge] retrieved top-{dense_config.top_k} for {len(run)} queries in "
        f"{retrieve_seconds:.3f}s ({latency_ms_per_query:.3f} ms/query, query encoding included)"
    )

    run_tag = "bge"
    trec_path = save_trec_run(run, Path(paths["runs_dir"]) / "bge.trec", run_tag)
    json_path = save_run_json(run, Path(paths["runs_dir"]) / "bge.json")
    print(f"[run_bge] wrote {trec_path} and {json_path}")

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
        "model": "bge",
        "config_path": args.config,
        "parameters": {"model": asdict(dense_config)},
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
            "num_vectors": len(corpus_text),
            "size_bytes": index_size_bytes,
        },
        "device": device,
    }
    metrics_path = Path(paths["metrics_dir"]) / "bge.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics_payload, indent=2))
    print(f"[run_bge] wrote {metrics_path}")

    manifest = build_manifest(
        experiment_id="exp-bge-001",
        dataset=ds_cfg["name"],
        split="test",
        model=dense_config.name,
        parameters=metrics_payload["parameters"],
        seed=cfg["seed"],
        device=device,
        runtime_seconds=total_seconds,
        status="complete",
        extra={
            "num_queries_evaluated": results["num_queries_evaluated"],
            "top_k": dense_config.top_k,
            "embedding_dim": embedding_dim,
            "index_size_bytes": index_size_bytes,
        },
    )
    manifest_path = save_manifest(manifest, paths["manifests_dir"])
    print(f"[run_bge] wrote {manifest_path}")

    print("\n=== BGE (test split, n={} queries) ===".format(results["num_queries_evaluated"]))
    for k, v in results["summary"].items():
        print(f"  {k:12s} {v:.4f}")
    print(f"  {'Latency':12s} {latency_ms_per_query:.3f} ms/query")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
