"""Tests for the TF-IDF baseline (M2), including hand-calculable examples
(Section 6 of the project spec: "educational tests validating small
hand-calculated examples").
"""

from __future__ import annotations

import math

import pytest

from biomedical_ir.preprocessing import PreprocessConfig
from biomedical_ir.tfidf import TfidfConfig, TfidfRetriever, toy_corpus


class TestHandComputedTfidf:
    """Manual derivation for toy_corpus() = {A: "cat dog cat", B: "dog bird",
    C: "cat bird bird"}, vocabulary {bird, cat, dog}, each term appearing in
    exactly 2 of the 3 documents.

    With smooth_idf=True: idf(t) = ln((1 + N) / (1 + df(t))) + 1
                                  = ln(4/3) + 1 ~= 1.28768   (same for every term here)
    With sublinear_tf=True: tf'(t, d) = 1 + ln(tf(t, d)) for tf > 0, else 0.

    Doc A: cat tf=2 -> tf'=1+ln2=1.6931; dog tf=1 -> tf'=1.0; bird=0
    Doc C: cat tf=1 -> tf'=1.0; bird tf=2 -> tf'=1.6931; dog=0

    After multiplying by the (shared) idf and L2-normalizing each document
    vector, query "cat bird" (tf'=1 for each, idf shared, L2-normalized to
    [1/sqrt2, 1/sqrt2]) should score doc C highest (heavy on "bird", the
    query's repeated-weight term via C's tf=2 "bird"), then A, then B
    (missing "cat" entirely).
    """

    def test_toy_corpus_shape(self):
        corpus = toy_corpus()
        assert set(corpus) == {"A", "B", "C"}

    def test_ranking_order_matches_manual_derivation(self):
        retriever = TfidfRetriever(TfidfConfig(top_k=10)).fit(toy_corpus())
        ranked = retriever.rank("cat bird")
        ranked_ids = [d for d, _ in ranked]
        assert ranked_ids == ["C", "A", "B"]

    def test_top_score_matches_manual_calculation(self):
        # Manually derived cosine(query, C): idf cancels (shared across all
        # terms in this corpus), leaving cos = (0.5085 + 0.8611) / sqrt(2)
        # ~= 0.9686 (see module docstring for the full derivation).
        retriever = TfidfRetriever(TfidfConfig(top_k=10)).fit(toy_corpus())
        ranked = retriever.rank("cat bird")
        top_doc, top_score = ranked[0]
        assert top_doc == "C"
        assert top_score == pytest.approx(0.9684, abs=1e-3)

    def test_document_missing_query_term_scores_lower(self):
        # Doc B has no "cat" at all -> should score strictly below A and C.
        retriever = TfidfRetriever(TfidfConfig(top_k=10)).fit(toy_corpus())
        scores = dict(retriever.rank("cat bird"))
        assert scores["B"] < scores["A"]
        assert scores["B"] < scores["C"]

    def test_idf_is_identical_across_terms_in_this_corpus(self):
        # Every one of {bird, cat, dog} appears in exactly 2/3 documents, so
        # sklearn's smoothed IDF should assign them literally the same
        # weight -- verified directly against the fitted vectorizer.
        retriever = TfidfRetriever(TfidfConfig(top_k=10)).fit(toy_corpus())
        idf = retriever.vectorizer.idf_
        vocab = retriever.vectorizer.vocabulary_
        expected_idf = math.log(4 / 3) + 1
        for term in ("bird", "cat", "dog"):
            assert idf[vocab[term]] == pytest.approx(expected_idf, abs=1e-9)


class TestTiesAndEdgeCases:
    def test_query_with_no_matching_terms_returns_zero_scores(self):
        retriever = TfidfRetriever(TfidfConfig(top_k=10)).fit(toy_corpus())
        ranked = retriever.rank("elephant")
        assert all(score == 0.0 for _, score in ranked)

    def test_empty_query_string_does_not_raise(self):
        retriever = TfidfRetriever(TfidfConfig(top_k=10)).fit(toy_corpus())
        ranked = retriever.rank("")
        assert len(ranked) == 3
        assert all(score == 0.0 for _, score in ranked)

    def test_tied_scores_break_ties_by_doc_id_ascending(self):
        # Two documents with the exact same content tie exactly; the
        # deterministic tie-break sorts by doc_id ascending.
        corpus = {"Z": "apple banana", "A": "apple banana", "M": "apple banana"}
        retriever = TfidfRetriever(TfidfConfig(top_k=10)).fit(corpus)
        ranked = retriever.rank("apple banana")
        assert [d for d, _ in ranked] == ["A", "M", "Z"]

    def test_top_k_truncates_results(self):
        retriever = TfidfRetriever(TfidfConfig(top_k=1)).fit(toy_corpus())
        ranked = retriever.rank("cat bird")
        assert len(ranked) == 1

    def test_top_k_larger_than_corpus_returns_all_docs(self):
        retriever = TfidfRetriever(TfidfConfig(top_k=1000)).fit(toy_corpus())
        ranked = retriever.rank("cat bird")
        assert len(ranked) == 3

    def test_rank_before_fit_raises(self):
        retriever = TfidfRetriever(TfidfConfig())
        with pytest.raises(RuntimeError):
            retriever.rank("cat")

    def test_malformed_corpus_with_empty_document_does_not_raise(self):
        corpus = {"A": "cat dog", "EMPTY": "", "B": "dog bird"}
        retriever = TfidfRetriever(TfidfConfig(top_k=10)).fit(corpus)
        ranked = retriever.rank("cat")
        assert len(ranked) == 3


class TestConfigLoading:
    def test_from_config_reads_tfidf_yaml_shape(self):
        cfg = {
            "tfidf": {
                "sublinear_tf": True,
                "norm": "l2",
                "smooth_idf": True,
                "use_idf": True,
                "ngram_range": [1, 1],
                "min_df": 1,
                "max_df": 1.0,
            },
            "retrieval": {"top_k": 100},
        }
        parsed = TfidfConfig.from_config(cfg)
        assert parsed.sublinear_tf is True
        assert parsed.norm == "l2"
        assert parsed.top_k == 100
        assert parsed.ngram_range == (1, 1)

    def test_rank_all_covers_every_query(self):
        retriever = TfidfRetriever(TfidfConfig(top_k=10)).fit(toy_corpus())
        queries = {"q1": "cat", "q2": "dog bird"}
        results = retriever.rank_all(queries)
        assert set(results.keys()) == {"q1", "q2"}


class TestPreprocessingIntegration:
    def test_lowercasing_makes_query_case_insensitive(self):
        retriever = TfidfRetriever(
            TfidfConfig(top_k=10), PreprocessConfig(lowercase=True)
        ).fit(toy_corpus())
        lower = dict(retriever.rank("CAT BIRD"))
        upper = dict(retriever.rank("cat bird"))
        assert lower == upper
