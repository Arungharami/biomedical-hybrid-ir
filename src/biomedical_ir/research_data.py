"""Pinned BEIR ingestion and explicit, leakage-safe tuning partitions."""

from __future__ import annotations

import hashlib
import random

from .data import NFCorpusData

BENCHMARKS = {"nfcorpus", "scifact", "trec-covid"}


def normalize_benchmark(corpus_rows, query_rows, qrel_rows):
    corpus, queries, qrels = {}, {}, {}
    for row in corpus_rows:
        key = str(row["_id"])
        if key in corpus:
            raise ValueError(f"Duplicate document: {key}")
        title, text = row.get("title") or "", row.get("text") or ""
        if not (title + text).strip():
            raise ValueError(f"Empty document: {key}")
        corpus[key] = {"title": title, "text": text}
    for row in query_rows:
        key = str(row["_id"])
        if key in queries:
            raise ValueError(f"Duplicate query: {key}")
        text = " ".join([row.get("title") or "", row.get("text") or ""]).strip()
        if not text:
            raise ValueError(f"Empty query: {key}")
        queries[key] = text
    for split, rows in qrel_rows.items():
        split = "dev" if split == "validation" else split
        if split in qrels:
            raise ValueError(f"Ambiguous tuning split: {split}")
        qrels[split] = {}
        for row in rows:
            qid, did = str(row["query-id"]), str(row["corpus-id"])
            raw = float(row["score"])
            if raw < 0 or not raw.is_integer():
                raise ValueError("Relevance must be a nonnegative integer")
            if qid not in queries or did not in corpus:
                raise ValueError(f"Dangling qrel: {qid}/{did}")
            docs = qrels[split].setdefault(qid, {})
            if did in docs:
                raise ValueError(f"Duplicate qrel: {split}/{qid}/{did}")
            docs[did] = int(raw)
    for left in qrels:
        for right in qrels:
            if left < right and set(qrels[left]) & set(qrels[right]):
                raise ValueError(f"Query-ID overlap: {left}/{right}")
    if not qrels.get("test"):
        raise ValueError("Nonempty official test qrels required")
    return NFCorpusData(corpus=corpus, queries=queries, qrels=qrels)


def define_tuning_split(data, seed=42, fraction=0.2):
    """Keep official dev; otherwise reserve train queries. Never split test."""
    if not 0 < fraction < 1:
        raise ValueError("Holdout fraction must be between 0 and 1")
    if data.qrels.get("dev"):
        policy = "official validation/dev"
    elif data.qrels.get("train"):
        keys = sorted(data.qrels["train"])
        if len(keys) < 2:
            raise ValueError("At least two training queries required for holdout")
        random.Random(seed).shuffle(keys)
        n = max(1, min(len(keys) - 1, int(len(keys) * fraction)))
        held_out = set(keys[:n])
        data.qrels["dev"] = {q: data.qrels["train"][q] for q in sorted(held_out)}
        data.qrels["train"] = {q: d for q, d in data.qrels["train"].items() if q not in held_out}
        policy = "seeded query-ID holdout from official train"
    else:
        policy = "no tuning split; fixed parameters required"
    ids = {s: sorted(rows) for s, rows in data.qrels.items()}
    text_sets = {s: {" ".join(data.queries[q].casefold().split()) for q in rows}
                 for s, rows in data.qrels.items()}
    overlap = {f"{a}/{b}": len(text_sets[a] & text_sets[b])
               for a in text_sets for b in text_sets if a < b}
    data.provenance.update(tuning_policy=policy, seed=seed, holdout_fraction=fraction,
                           split_query_ids=ids, normalized_query_text_overlap=overlap)
    if overlap.get("dev/test", 0):
        raise ValueError("Normalized query-text overlap between dev and test; resolve before tuning")
    return data


def load_benchmark(name, cache_dir="data/cache/research", seed=42):
    if name not in BENCHMARKS:
        raise ValueError(f"Unknown benchmark: {name}")
    from datasets import get_dataset_split_names, load_dataset
    from huggingface_hub import HfApi

    dataset, qrel_dataset = f"BeIR/{name}", f"BeIR/{name}-qrels"
    api = HfApi()
    dataset_sha = api.dataset_info(dataset).sha
    qrels_sha = api.dataset_info(qrel_dataset).sha
    corpus = load_dataset(dataset, "corpus", split="corpus", revision=dataset_sha, cache_dir=cache_dir)
    queries = load_dataset(dataset, "queries", split="queries", revision=dataset_sha, cache_dir=cache_dir)
    splits = get_dataset_split_names(qrel_dataset, revision=qrels_sha)
    rows = {s: load_dataset(qrel_dataset, split=s, revision=qrels_sha, cache_dir=cache_dir)
            for s in splits}
    data = normalize_benchmark(corpus, queries, rows)
    data.provenance = {"dataset": dataset, "dataset_sha": dataset_sha,
                       "qrels_dataset": qrel_dataset, "qrels_sha": qrels_sha,
                       "document_count": len(data.corpus), "query_count": len(data.queries)}
    define_tuning_split(data, seed=seed)
    identity = f"{dataset_sha}:{qrels_sha}:{seed}"
    data.provenance["identity"] = hashlib.sha256(identity.encode()).hexdigest()
    return data
