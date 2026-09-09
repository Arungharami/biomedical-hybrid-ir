#!/usr/bin/env python
"""Download NFCorpus (or reuse cache), validate it, and write audit artifacts.

Produces:
    data/processed/dataset_stats.json
    data/processed/corpus_stats.json
    data/processed/query_stats.json

Usage:
    python scripts/audit_dataset.py [--config configs/default.yaml] [--from-raw]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, median

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from biomedical_ir.data import load_nfcorpus, load_nfcorpus_from_raw  # noqa: E402
from biomedical_ir.utils import load_config  # noqa: E402
from biomedical_ir.validation import validate_nfcorpus  # noqa: E402


def word_count(text: str) -> int:
    return len(text.split())


def compute_corpus_stats(data) -> dict:
    title_lens = [word_count(d["title"]) for d in data.corpus.values()]
    text_lens = [word_count(d["text"]) for d in data.corpus.values()]
    docs_with_title = sum(1 for d in data.corpus.values() if d["title"].strip())
    vocab = set()
    for d in data.corpus.values():
        vocab.update((d["title"] + " " + d["text"]).lower().split())

    return {
        "num_documents": len(data.corpus),
        "documents_with_nonempty_title": docs_with_title,
        "title_word_count": _dist(title_lens),
        "body_word_count": _dist(text_lens),
        "approx_vocabulary_size": len(vocab),
    }


def compute_query_stats(data) -> dict:
    lens = [word_count(q) for q in data.queries.values()]
    per_split = {}
    for split, split_qrels in data.qrels.items():
        if split.startswith("_"):
            continue
        n_rel_per_query = [len(rels) for rels in split_qrels.values()]
        rel_values = Counter(r for rels in split_qrels.values() for r in rels.values())
        per_split[split] = {
            "num_queries_with_qrels": len(split_qrels),
            "relevant_docs_per_query": _dist(n_rel_per_query),
            "relevance_label_distribution": dict(sorted(rel_values.items())),
        }

    return {
        "num_queries_total": len(data.queries),
        "query_word_count": _dist(lens),
        "by_split": per_split,
    }


def _dist(values: list[int]) -> dict:
    if not values:
        return {"min": None, "max": None, "mean": None, "median": None, "n": 0}
    return {
        "min": min(values),
        "max": max(values),
        "mean": round(mean(values), 2),
        "median": median(values),
        "n": len(values),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--from-raw", action="store_true", help="reuse cached data/raw dump, no network")
    args = parser.parse_args()

    cfg = load_config(args.config)
    ds_cfg = cfg["dataset"]
    processed_dir = Path(ds_cfg["processed_dir"])
    processed_dir.mkdir(parents=True, exist_ok=True)

    if args.from_raw:
        data = load_nfcorpus_from_raw(ds_cfg["raw_dir"])
    else:
        data = load_nfcorpus(
            cache_dir=ds_cfg["cache_dir"],
            raw_dir=ds_cfg["raw_dir"],
            splits=tuple(ds_cfg["splits"]),
        )

    report = validate_nfcorpus(data)

    corpus_stats = compute_corpus_stats(data)
    query_stats = compute_query_stats(data)
    dataset_stats = {
        "provenance": data.provenance,
        "validation": report.to_dict(),
        "corpus_size": len(data.corpus),
        "query_count": len(data.queries),
        "qrel_counts": {s: len(v) for s, v in data.qrels.items() if not s.startswith("_")},
        "splits": {
            "train": {"role": "development (not used for final evaluation)"},
            "dev": {"role": "parameter tuning / model selection only"},
            "test": {"role": "final evaluation only - never used for tuning"},
        },
    }

    (processed_dir / "dataset_stats.json").write_text(json.dumps(dataset_stats, indent=2))
    (processed_dir / "corpus_stats.json").write_text(json.dumps(corpus_stats, indent=2))
    (processed_dir / "query_stats.json").write_text(json.dumps(query_stats, indent=2))

    print(f"Validation OK: {report.ok}")
    if report.errors:
        print("ERRORS:")
        for e in report.errors:
            print(f"  - {e}")
    if report.warnings:
        print("WARNINGS:")
        for w in report.warnings:
            print(f"  - {w}")
    print(f"Wrote stats to {processed_dir}")

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
