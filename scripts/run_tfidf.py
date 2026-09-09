#!/usr/bin/env python
"""M2: TF-IDF baseline -- fit on the full NFCorpus corpus, retrieve top-k for
every TEST split query, evaluate against the real test qrels, and write
run/metrics/manifest artifacts.

Produces:
    results/runs/tfidf.trec, results/runs/tfidf.json
    results/metrics/tfidf.json
    results/manifests/exp-tfidf-001.json

Usage:
    python scripts/run_tfidf.py [--config configs/tfidf.yaml]
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
from biomedical_ir.evaluation import evaluate_run, save_run_json, save_trec_run  # noqa: E402
from biomedical_ir.manifests import build_manifest, save_manifest  # noqa: E402
from biomedical_ir.preprocessing import PreprocessConfig  # noqa: E402
from biomedical_ir.tfidf import TfidfConfig, TfidfRetriever  # noqa: E402
from biomedical_ir.utils import ensure_dirs, load_config, set_seed  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/tfidf.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    set_seed(cfg["seed"])

    ds_cfg = cfg["dataset"]
    paths = cfg["paths"]
    doc_comp = cfg["document_composition"]
    ensure_dirs(paths["runs_dir"], paths["metrics_dir"], paths["manifests_dir"])

    print("[run_tfidf] loading NFCorpus from raw cache (no network) ...")
    data = load_nfcorpus_from_raw(ds_cfg["raw_dir"])
    print(f"[run_tfidf] corpus={len(data.corpus)} docs, queries={len(data.queries)}")

    test_qrels = data.qrels.get("test", {})
    test_qids = sorted(test_qrels.keys())
    test_queries = {qid: data.queries[qid] for qid in test_qids if qid in data.queries}
    print(f"[run_tfidf] test split: {len(test_queries)} queries with qrels")

    corpus_text = {
        doc_id: compose_document_text(
            d.get("title", ""), d.get("text", ""), doc_comp["strategy"], doc_comp["separator"]
        )
        for doc_id, d in data.corpus.items()
    }

    preprocess_config = PreprocessConfig.from_config(cfg)
    tfidf_config = TfidfConfig.from_config(cfg)
    print(f"[run_tfidf] preprocess={preprocess_config} tfidf={tfidf_config}")

    retriever = TfidfRetriever(tfidf_config, preprocess_config)

    fit_start = time.perf_counter()
    retriever.fit(corpus_text)
    fit_seconds = time.perf_counter() - fit_start
    print(f"[run_tfidf] fit complete in {fit_seconds:.3f}s (vocab size ~ "
          f"{len(retriever.vectorizer.vocabulary_)})")

    retrieve_start = time.perf_counter()
    run = retriever.rank_all(test_queries, top_k=tfidf_config.top_k)
    retrieve_seconds = time.perf_counter() - retrieve_start
    latency_ms_per_query = (retrieve_seconds / len(test_queries)) * 1000 if test_queries else 0.0
    print(
        f"[run_tfidf] retrieved top-{tfidf_config.top_k} for {len(run)} queries in "
        f"{retrieve_seconds:.3f}s ({latency_ms_per_query:.3f} ms/query)"
    )

    run_tag = "tfidf"
    trec_path = save_trec_run(run, Path(paths["runs_dir"]) / "tfidf.trec", run_tag)
    json_path = save_run_json(run, Path(paths["runs_dir"]) / "tfidf.json")
    print(f"[run_tfidf] wrote {trec_path} and {json_path}")

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
    total_seconds = fit_seconds + retrieve_seconds

    metrics_payload = {
        "model": "tfidf",
        "config_path": args.config,
        "parameters": {
            "tfidf": asdict(tfidf_config),
            "lexical_preprocessing": {
                "unicode_normalize": preprocess_config.unicode_normalize,
                "lowercase": preprocess_config.lowercase,
                "strip_punctuation": preprocess_config.strip_punctuation,
                "remove_stopwords": preprocess_config.remove_stopwords,
                "tokenizer": preprocess_config.tokenizer,
                "min_token_len": preprocess_config.min_token_len,
            },
        },
        "split": "test",
        "num_queries_evaluated": results["num_queries_evaluated"],
        "dropped_queries_not_in_qrels": results["dropped_queries_not_in_qrels"],
        "metrics": results["summary"],
        "timing": {
            "fit_seconds": round(fit_seconds, 4),
            "retrieve_seconds": round(retrieve_seconds, 4),
            "total_seconds": round(total_seconds, 4),
            "latency_ms_per_query": round(latency_ms_per_query, 4),
        },
    }
    metrics_path = Path(paths["metrics_dir"]) / "tfidf.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics_payload, indent=2))
    print(f"[run_tfidf] wrote {metrics_path}")

    manifest = build_manifest(
        experiment_id="exp-tfidf-001",
        dataset=ds_cfg["name"],
        split="test",
        model="tfidf",
        parameters=metrics_payload["parameters"],
        seed=cfg["seed"],
        device="cpu",
        runtime_seconds=total_seconds,
        status="complete",
        extra={"num_queries_evaluated": results["num_queries_evaluated"], "top_k": tfidf_config.top_k},
    )
    manifest_path = save_manifest(manifest, paths["manifests_dir"])
    print(f"[run_tfidf] wrote {manifest_path}")

    print("\n=== TF-IDF (test split, n={} queries) ===".format(results["num_queries_evaluated"]))
    for k, v in results["summary"].items():
        print(f"  {k:12s} {v:.4f}")
    print(f"  {'Latency':12s} {latency_ms_per_query:.3f} ms/query")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
