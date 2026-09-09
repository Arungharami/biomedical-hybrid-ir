"""Tests for NFCorpus ingestion, composition, and validation.

These use small synthetic NFCorpusData fixtures (no network access) so they
run fast in CI; the real Hugging Face load is exercised manually via
scripts/audit_dataset.py and the dataset audit notebook, not in unit tests.
"""

from __future__ import annotations

import pytest

from biomedical_ir.data import NFCorpusData, compose_document_text
from biomedical_ir.validation import validate_nfcorpus


def make_clean_data() -> NFCorpusData:
    corpus = {
        "D1": {"title": "Statins and Cancer", "text": "Statins may reduce cancer risk."},
        "D2": {"title": "", "text": "A document with no title."},
        "D3": {"title": "Diet", "text": "Diet affects health outcomes."},
    }
    queries = {"Q1": "statins cancer risk", "Q2": "diet health", "Q3": "vitamin D deficiency"}
    # Disjoint query IDs per split, mirroring the real BEIR NFCorpus splits.
    qrels = {
        "train": {"Q1": {"D1": 1}},
        "dev": {"Q2": {"D3": 2}},
        "test": {"Q3": {"D1": 2, "D3": 1}},
    }
    provenance = {
        "duplicate_corpus_ids": {},
        "duplicate_query_ids": {},
        "corpus_size": len(corpus),
        "query_count": len(queries),
    }
    return NFCorpusData(corpus=corpus, queries=queries, qrels=qrels, provenance=provenance)


class TestCleanData:
    def test_valid_dataset_passes(self):
        report = validate_nfcorpus(make_clean_data())
        assert report.ok
        assert report.errors == []

    def test_stats_are_populated(self):
        report = validate_nfcorpus(make_clean_data())
        assert report.stats["corpus_size"] == 3
        assert report.stats["query_count"] == 3
        assert report.stats["qrel_counts"] == {"train": 1, "dev": 1, "test": 1}


class TestDuplicateIDs:
    def test_duplicate_document_ids_flagged(self):
        data = make_clean_data()
        data.provenance["duplicate_corpus_ids"] = {"D1": 2}
        report = validate_nfcorpus(data)
        assert not report.ok
        assert any("Duplicate document IDs" in e for e in report.errors)

    def test_duplicate_query_ids_flagged(self):
        data = make_clean_data()
        data.provenance["duplicate_query_ids"] = {"Q1": 2}
        report = validate_nfcorpus(data)
        assert not report.ok
        assert any("Duplicate query IDs" in e for e in report.errors)


class TestMissingReferences:
    def test_qrel_references_missing_document(self):
        data = make_clean_data()
        data.qrels["test"]["Q3"]["D999"] = 1  # D999 not in corpus
        report = validate_nfcorpus(data)
        assert not report.ok
        assert any("absent from the corpus" in e for e in report.errors)

    def test_qrel_references_missing_query(self):
        data = make_clean_data()
        data.qrels["test"]["Q999"] = {"D1": 1}  # Q999 not in queries
        report = validate_nfcorpus(data)
        assert not report.ok
        assert any("absent from the queries set" in e for e in report.errors)


class TestEmptyFields:
    def test_empty_query_string_flagged(self):
        data = make_clean_data()
        data.queries["Q3"] = "   "
        report = validate_nfcorpus(data)
        assert not report.ok
        assert any("empty strings" in e for e in report.errors)

    def test_empty_document_is_warning_not_error(self):
        data = make_clean_data()
        data.corpus["D4"] = {"title": "", "text": ""}
        report = validate_nfcorpus(data)
        # An empty document is suspicious but not necessarily a leakage/integrity
        # bug, so it is a warning rather than a hard error.
        assert any("empty title and empty text" in w for w in report.warnings)


class TestSplitIntegrity:
    def test_split_overlap_is_an_error(self):
        data = make_clean_data()
        data.qrels["dev"]["Q1"] = {"D1": 1}  # Q1 already in train -> overlap
        report = validate_nfcorpus(data)
        assert not report.ok
        assert any("overlap" in e.lower() for e in report.errors)

    def test_empty_split_is_a_warning(self):
        data = make_clean_data()
        data.qrels["dev"] = {}
        report = validate_nfcorpus(data)
        assert any("zero queries" in w for w in report.warnings)


class TestRelevanceLabelTypes:
    def test_non_castable_label_flagged(self):
        data = make_clean_data()
        data.qrels["test"]["Q3"]["D2"] = "not-a-number"
        report = validate_nfcorpus(data)
        assert not report.ok
        assert any("not integer-castable" in e for e in report.errors)


class TestDocumentComposition:
    def test_title_and_body_both_present(self):
        out = compose_document_text("Title", "Body text", separator=" [SEP] ")
        assert out == "Title [SEP] Body text"

    def test_title_only(self):
        assert compose_document_text("Title", "") == "Title"

    def test_body_only(self):
        assert compose_document_text("", "Body text") == "Body text"

    def test_both_empty(self):
        assert compose_document_text("", "") == ""

    def test_whitespace_stripped(self):
        out = compose_document_text("  Title  ", "  Body  ")
        assert out == "Title [SEP] Body"

    def test_unknown_strategy_raises(self):
        with pytest.raises(ValueError):
            compose_document_text("T", "B", strategy="bogus")
