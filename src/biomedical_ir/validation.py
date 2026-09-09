"""Automatic dataset validation for NFCorpus (Section 3 of the project spec).

Checks performed:
  - duplicate document IDs / duplicate query IDs
  - documents referenced by qrels that are missing from the corpus
  - queries referenced by qrels that are missing from the queries set
  - empty query strings / empty documents
  - train/dev/test split integrity (each split's query IDs are a subset of
    the queries set; splits do not silently overlap in a way that would leak
    tuning queries into the test split)
  - relevance label types (must be int-castable)
  - schema consistency (corpus rows have title+text keys, etc.)

Produces a structured report; never repairs or fabricates data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .data import NFCorpusData


@dataclass
class ValidationReport:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.ok = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "stats": self.stats,
        }


def validate_nfcorpus(data: NFCorpusData) -> ValidationReport:
    report = ValidationReport()

    # --- duplicate IDs (from provenance captured at load time) ---
    dup_corpus = data.provenance.get("duplicate_corpus_ids", {})
    dup_queries = data.provenance.get("duplicate_query_ids", {})
    if dup_corpus:
        report.add_error(f"Duplicate document IDs found: {len(dup_corpus)} (e.g. {list(dup_corpus)[:5]})")
    if dup_queries:
        report.add_error(f"Duplicate query IDs found: {len(dup_queries)} (e.g. {list(dup_queries)[:5]})")

    # --- schema consistency ---
    empty_docs = [did for did, d in data.corpus.items() if not (d.get("title") or d.get("text"))]
    if empty_docs:
        report.add_warning(f"{len(empty_docs)} documents have both empty title and empty text")

    empty_queries = [qid for qid, q in data.queries.items() if not q or not q.strip()]
    if empty_queries:
        report.add_error(f"{len(empty_queries)} queries are empty strings")

    for did, d in list(data.corpus.items())[:0]:  # schema shape already enforced by data.py
        pass
    bad_schema = [did for did, d in data.corpus.items() if "title" not in d or "text" not in d]
    if bad_schema:
        report.add_error(f"{len(bad_schema)} corpus rows missing 'title' or 'text' keys")

    # --- qrels referential integrity + label types ---
    missing_docs_total = 0
    missing_queries_total = 0
    bad_label_total = 0
    for split, split_qrels in data.qrels.items():
        if split.startswith("_"):
            continue
        for qid, doc_rels in split_qrels.items():
            if qid not in data.queries:
                missing_queries_total += 1
            for did, rel in doc_rels.items():
                if did not in data.corpus:
                    missing_docs_total += 1
                if not isinstance(rel, int):
                    try:
                        int(rel)
                    except (TypeError, ValueError):
                        bad_label_total += 1

    if missing_docs_total:
        report.add_error(
            f"{missing_docs_total} qrel entries reference document IDs absent from the corpus"
        )
    if missing_queries_total:
        report.add_error(
            f"{missing_queries_total} qrel entries reference query IDs absent from the queries set"
        )
    if bad_label_total:
        report.add_error(f"{bad_label_total} qrel relevance labels are not integer-castable")

    load_errors = data.qrels.get("_load_errors", {})
    for split, err in load_errors.items():
        report.add_error(f"Failed to load qrels for split '{split}': {err}")

    # --- train/dev/test split integrity ---
    splits = [s for s in data.qrels if not s.startswith("_")]
    split_query_ids = {s: set(data.qrels[s].keys()) for s in splits}
    for s in splits:
        if len(split_query_ids[s]) == 0:
            report.add_warning(f"Split '{s}' has zero queries with qrels")

    overlaps = {}
    split_list = sorted(split_query_ids)
    for i, s1 in enumerate(split_list):
        for s2 in split_list[i + 1 :]:
            overlap = split_query_ids[s1] & split_query_ids[s2]
            if overlap:
                overlaps[f"{s1}∩{s2}"] = len(overlap)
    if overlaps:
        # NFCorpus's official BEIR split assigns disjoint query sets per split;
        # any overlap is reported so tuning/test leakage can never happen silently.
        report.add_error(f"Query ID overlap between splits (would risk train/dev/test leakage): {overlaps}")

    report.stats = {
        "corpus_size": len(data.corpus),
        "query_count": len(data.queries),
        "qrel_counts": {s: len(data.qrels.get(s, {})) for s in splits},
        "empty_documents": len(empty_docs),
        "empty_queries": len(empty_queries),
        "duplicate_document_ids": len(dup_corpus),
        "duplicate_query_ids": len(dup_queries),
        "missing_doc_references_in_qrels": missing_docs_total,
        "missing_query_references_in_qrels": missing_queries_total,
        "split_overlaps": overlaps,
    }
    return report
