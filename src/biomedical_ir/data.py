"""NFCorpus ingestion from Hugging Face (BeIR/nfcorpus).

The canonical BeIR NFCorpus release on Hugging Face is split across three
dataset repos:
  - ``BeIR/nfcorpus``            (config "corpus")  -> documents
  - ``BeIR/nfcorpus``            (config "queries")  -> queries
  - ``BeIR/nfcorpus-qrels``      (splits "train"/"dev"/"test") -> relevance judgments

This module downloads and caches all three, and normalizes them into plain
Python dict-of-dicts structures (the standard BEIR in-memory format):

    corpus  = {doc_id:   {"title": str, "text": str}}
    queries = {query_id: str}
    qrels   = {split: {query_id: {doc_id: int_relevance}}}

All IDs are used exactly as supplied by the dataset -- nothing is renumbered
or fabricated.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .utils import REPO_ROOT

DATASET_NAME = "BeIR/nfcorpus"
QRELS_DATASET_NAME = "BeIR/nfcorpus-qrels"
SPLITS = ("train", "dev", "test")


@dataclass
class NFCorpusData:
    corpus: dict[str, dict[str, str]] = field(default_factory=dict)
    queries: dict[str, str] = field(default_factory=dict)
    qrels: dict[str, dict[str, dict[str, int]]] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)


def load_nfcorpus(
    cache_dir: str | Path = "./data/cache/huggingface",
    raw_dir: str | Path = "./data/raw/nfcorpus",
    splits: tuple[str, ...] = SPLITS,
    save_raw: bool = True,
) -> NFCorpusData:
    """Download (or reuse cache) and return the full NFCorpus corpus/queries/qrels."""
    from collections import Counter

    from datasets import load_dataset

    cache_dir = str(cache_dir)
    raw_dir = Path(raw_dir)

    corpus_ds = load_dataset(DATASET_NAME, "corpus", cache_dir=cache_dir)["corpus"]
    queries_ds = load_dataset(DATASET_NAME, "queries", cache_dir=cache_dir)["queries"]

    # Duplicate IDs would silently collapse in a plain dict comprehension, so
    # count raw occurrences first and preserve the counts for validation.py.
    corpus_id_counts = Counter(corpus_ds["_id"])
    query_id_counts = Counter(queries_ds["_id"])

    corpus: dict[str, dict[str, str]] = {}
    for row in corpus_ds:
        corpus[row["_id"]] = {
            "title": row.get("title", "") or "",
            "text": row.get("text", "") or "",
        }

    queries: dict[str, str] = {}
    for row in queries_ds:
        # NFCorpus queries carry their text in the "text" field; "title" is
        # typically empty for this dataset but is folded in defensively in
        # case a title is ever present.
        title = (row.get("title") or "").strip()
        text = (row.get("text") or "").strip()
        queries[row["_id"]] = f"{title} {text}".strip() if title else text

    qrels: dict[str, dict[str, dict[str, int]]] = {}
    for split in splits:
        try:
            qrels_ds = load_dataset(QRELS_DATASET_NAME, split=split, cache_dir=cache_dir)
        except Exception as e:  # dataset/split may not exist -- document, don't fabricate
            qrels[split] = {}
            qrels.setdefault("_load_errors", {})[split] = str(e)
            continue
        split_qrels: dict[str, dict[str, int]] = {}
        for row in qrels_ds:
            qid = str(row["query-id"])
            did = str(row["corpus-id"])
            rel = int(row["score"])
            split_qrels.setdefault(qid, {})[did] = rel
        qrels[split] = split_qrels

    provenance = {
        "hf_dataset": DATASET_NAME,
        "hf_qrels_dataset": QRELS_DATASET_NAME,
        "corpus_config": "corpus",
        "queries_config": "queries",
        "splits_requested": list(splits),
        "corpus_size": len(corpus),
        "query_count": len(queries),
        "qrel_counts": {s: len(qrels.get(s, {})) for s in splits},
        "raw_corpus_row_count": len(corpus_ds),
        "raw_query_row_count": len(queries_ds),
        "duplicate_corpus_ids": {k: v for k, v in corpus_id_counts.items() if v > 1},
        "duplicate_query_ids": {k: v for k, v in query_id_counts.items() if v > 1},
    }

    data = NFCorpusData(corpus=corpus, queries=queries, qrels=qrels, provenance=provenance)

    if save_raw:
        raw_dir.mkdir(parents=True, exist_ok=True)
        _dump_jsonl(raw_dir / "corpus.jsonl", corpus)
        _dump_jsonl(raw_dir / "queries.jsonl", queries)
        for split in splits:
            with open(raw_dir / f"qrels_{split}.json", "w") as f:
                json.dump(qrels.get(split, {}), f)
        with open(raw_dir / "provenance.json", "w") as f:
            json.dump(provenance, f, indent=2)

    return data


def _dump_jsonl(path: Path, mapping: dict) -> None:
    with open(path, "w") as f:
        for key, value in mapping.items():
            if isinstance(value, dict):
                f.write(json.dumps({"_id": key, **value}) + "\n")
            else:
                f.write(json.dumps({"_id": key, "text": value}) + "\n")


def load_nfcorpus_from_raw(raw_dir: str | Path = "./data/raw/nfcorpus") -> NFCorpusData:
    """Reload a previously-cached NFCorpus dump without hitting the network."""
    raw_dir = Path(raw_dir)
    corpus = {}
    with open(raw_dir / "corpus.jsonl") as f:
        for line in f:
            row = json.loads(line)
            corpus[row["_id"]] = {"title": row.get("title", ""), "text": row.get("text", "")}

    queries = {}
    with open(raw_dir / "queries.jsonl") as f:
        for line in f:
            row = json.loads(line)
            queries[row["_id"]] = row.get("text", "")

    qrels = {}
    for split in SPLITS:
        p = raw_dir / f"qrels_{split}.json"
        if p.exists():
            with open(p) as f:
                qrels[split] = json.load(f)

    provenance = {}
    prov_path = raw_dir / "provenance.json"
    if prov_path.exists():
        with open(prov_path) as f:
            provenance = json.load(f)

    return NFCorpusData(corpus=corpus, queries=queries, qrels=qrels, provenance=provenance)


def compose_document_text(
    title: str,
    text: str,
    strategy: str = "title_sep_body",
    separator: str = " [SEP] ",
) -> str:
    """Compose a single retrievable string from a document's title/body.

    Mirrors ``configs/default.yaml -> document_composition``. When both
    fields exist, uses ``title {separator} text``; falls back gracefully
    when either field is empty so no document collapses to an empty string
    unless both fields genuinely are empty.
    """
    title = (title or "").strip()
    text = (text or "").strip()
    if strategy == "title_sep_body":
        if title and text:
            return f"{title}{separator}{text}"
        return title or text
    if strategy == "body_only":
        return text or title
    raise ValueError(f"Unknown document_composition.strategy: {strategy}")
