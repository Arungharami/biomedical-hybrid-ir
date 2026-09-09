"""Tests for the transparent from-scratch BM25 baseline (M2), including
hand-calculable examples (Section 6 of the project spec).
"""

from __future__ import annotations

import math

import pytest

from biomedical_ir.bm25 import BM25Config, BM25Retriever, toy_corpus


class TestHandComputedBM25:
    """Manual derivation for toy_corpus() = {A: "cat dog cat", B: "dog bird",
    C: "cat bird bird"}, k1=1.2, b=0.75, N=3, avgdl=(3+2+3)/3=2.6667.

    Every term (bird, cat, dog) appears in exactly 2 of 3 documents, so
    idf(t) = ln((3 - 2 + 0.5) / (2 + 0.5)) = ln(0.6) ~= -0.51083 for ALL
    three terms -- a deliberately chosen corpus size where the classical
    Robertson IDF (no +1 inside the log, see bm25.py's module docstring)
    goes negative, which is a documented, correct property of the formula,
    not a bug. Because idf is identical (and negative) for every term here,
    a HIGHER term frequency makes a document's score MORE negative (worse),
    inverting the "more matches = better" intuition for this particular toy
    corpus -- this is exactly why the exact formula must be stated
    precisely rather than assumed.

    score(D, "cat bird") worked out by hand (see bm25.py docstring for the
    BM25 formula):
      norm(dl=3) = k1*(1-b+b*3/avgdl) = 1.2*(0.25+0.75*1.125)  = 1.3125
      norm(dl=2) = 1.2*(0.25+0.75*0.75)                        = 0.975
      A: cat tf=2 -> idf*2*2.2/(2+1.3125) = -0.51083*1.32836   = -0.67853
         bird tf=0 -> 0                     => total A          = -0.67853
      B: bird tf=1 -> idf*1*2.2/(1+0.975)  = -0.51083*1.11392  = -0.56902
         cat tf=0 -> 0                      => total B          = -0.56902
      C: cat tf=1 -> idf*1*2.2/(1+1.3125)  = -0.51083*0.95135  = -0.48598
         bird tf=2 -> idf*2*2.2/(2+1.3125) = -0.51083*1.32836  = -0.67853
                                             => total C          = -1.16451
    Ranking (highest/least-negative score first): B > A > C.
    """

    def test_toy_corpus_shape(self):
        corpus = toy_corpus()
        assert set(corpus) == {"A", "B", "C"}

    def test_idf_matches_manual_derivation(self):
        retriever = BM25Retriever(BM25Config()).fit(toy_corpus())
        expected_idf = math.log((3 - 2 + 0.5) / (2 + 0.5))
        for term in ("bird", "cat", "dog"):
            assert retriever._idf_cache[term] == pytest.approx(expected_idf, abs=1e-9)
        assert expected_idf < 0  # documented property of this toy corpus

    def test_avgdl_matches_manual_derivation(self):
        retriever = BM25Retriever(BM25Config()).fit(toy_corpus())
        assert retriever.avgdl == pytest.approx(8 / 3, abs=1e-9)

    def test_document_scores_match_manual_derivation(self):
        retriever = BM25Retriever(BM25Config(top_k=10)).fit(toy_corpus())
        query_tokens = ["cat", "bird"]
        assert retriever.score(query_tokens, "A") == pytest.approx(-0.67853, abs=1e-4)
        assert retriever.score(query_tokens, "B") == pytest.approx(-0.56902, abs=1e-4)
        assert retriever.score(query_tokens, "C") == pytest.approx(-1.16451, abs=1e-4)

    def test_ranking_order_matches_manual_derivation(self):
        retriever = BM25Retriever(BM25Config(top_k=10)).fit(toy_corpus())
        ranked = retriever.rank("cat bird")
        assert [d for d, _ in ranked] == ["B", "A", "C"]


class TestTermSaturationAndLengthNormalization:
    """Larger, less-degenerate corpus (rare terms => positive IDF) to check
    the two BM25 mechanisms in their more intuitive regime."""

    @staticmethod
    def _corpus():
        return {
            "D1": "diabetes diabetes diabetes treatment",
            "D2": "diabetes treatment insulin therapy",
            "D3": ("insulin therapy glucose metabolism blood sugar levels "
                   "diabetes patient care management long document padding "
                   "extra words extra words extra words extra words"),
            "D4": "vitamin c supplement immune system",
            "D5": "vitamin d bone health calcium absorption",
        }

    def test_rare_term_has_positive_idf(self):
        retriever = BM25Retriever(BM25Config()).fit(self._corpus())
        # "calcium" appears in exactly 1/5 documents -> positive idf.
        assert retriever._idf_cache["calcium"] > 0

    def test_term_frequency_saturation_diminishing_returns(self):
        # Dedicated corpus with a RARE term (df=2/5 -> positive idf, unlike
        # "diabetes" above) so that "more occurrences = higher score" holds
        # in the expected direction, isolating the saturation effect from
        # the sign of idf. D1's length is held constant (5 tokens) across
        # both variants so length normalization cannot confound the result.
        def make_corpus(d1_text: str) -> dict[str, str]:
            return {
                "D1": d1_text,
                "D2": "other words only here padding",
                "D3": "more filler content padding words",
                "D4": "additional padding text words only",
                "D5": "target appears once here too padding",
            }

        retriever_tf3 = BM25Retriever(BM25Config()).fit(
            make_corpus("target target target filler filler")
        )
        score_tf3 = retriever_tf3.score(["target"], "D1")

        retriever_tf1 = BM25Retriever(BM25Config()).fit(
            make_corpus("target filler filler filler filler")
        )
        score_tf1 = retriever_tf1.score(["target"], "D1")

        assert retriever_tf3._idf_cache["target"] > 0  # sanity: rare term, positive idf
        # tf=3 scores higher than tf=1, but less than 3x -- diminishing returns.
        assert score_tf3 > score_tf1
        assert score_tf3 < 3 * score_tf1

    def test_longer_document_penalized_at_equal_term_frequency(self):
        retriever = BM25Retriever(BM25Config()).fit(self._corpus())
        # D2 (short, tf("insulin")=1) should score higher than D3 (long,
        # tf("insulin")=1) for the same query term, due to length normalization.
        assert retriever.score(["insulin"], "D2") > retriever.score(["insulin"], "D3")

    def test_b_zero_disables_length_normalization(self):
        # With b=0, document length no longer affects the score at all.
        retriever = BM25Retriever(BM25Config(k1=1.2, b=0.0)).fit(self._corpus())
        norm_d2 = retriever.config.b  # sanity: config actually holds b=0
        assert norm_d2 == 0.0
        # score should now depend purely on tf and idf, not |D|/avgdl
        s_short = retriever.score(["insulin"], "D2")
        s_long = retriever.score(["insulin"], "D3")
        assert s_short == pytest.approx(s_long, abs=1e-9)


class TestConfigLoading:
    def test_from_config_reads_bm25_yaml_shape(self):
        cfg = {"bm25": {"k1": 1.2, "b": 0.75}, "retrieval": {"top_k": 100}}
        parsed = BM25Config.from_config(cfg)
        assert parsed.k1 == 1.2
        assert parsed.b == 0.75
        assert parsed.top_k == 100

    def test_default_config_matches_bm25_yaml_frozen_values(self):
        parsed = BM25Config()
        assert parsed.k1 == 1.2
        assert parsed.b == 0.75


class TestTiesAndEdgeCases:
    def test_query_with_no_matching_terms_returns_empty(self):
        retriever = BM25Retriever(BM25Config(top_k=10)).fit(toy_corpus())
        assert retriever.rank("elephant") == []

    def test_empty_query_string_returns_empty(self):
        retriever = BM25Retriever(BM25Config(top_k=10)).fit(toy_corpus())
        assert retriever.rank("") == []

    def test_rank_before_fit_raises(self):
        retriever = BM25Retriever(BM25Config())
        with pytest.raises(RuntimeError):
            retriever.rank("cat")

    def test_top_k_truncates_results(self):
        retriever = BM25Retriever(BM25Config(top_k=1)).fit(toy_corpus())
        ranked = retriever.rank("cat bird")
        assert len(ranked) == 1

    def test_malformed_corpus_with_empty_document_does_not_raise(self):
        corpus = {"A": "cat dog", "EMPTY": "", "B": "dog bird"}
        retriever = BM25Retriever(BM25Config(top_k=10)).fit(corpus)
        ranked = retriever.rank("cat")
        assert all(d != "EMPTY" for d, _ in ranked)  # empty doc never matches any term

    def test_rank_all_covers_every_query(self):
        retriever = BM25Retriever(BM25Config(top_k=10)).fit(toy_corpus())
        results = retriever.rank_all({"q1": "cat", "q2": "dog bird"})
        assert set(results.keys()) == {"q1", "q2"}


class TestCrossCheckAgainstRankBm25:
    """Optional cross-check against the third-party `rank_bm25` library
    (Section 6 allows this as an optional sanity check; skipped cleanly if
    the package is not installed, since it is not a hard dependency).

    Uses query terms with POSITIVE idf only ("insulin", "therapy", each
    appearing in 2/5 corpus documents). ``rank_bm25.BM25Okapi`` applies an
    epsilon correction that replaces any NEGATIVE idf with
    ``eps * average_idf`` instead of using the classical formula's raw
    (negative) value -- a deliberate departure from Robertson & Zaragoza
    that this project's transparent implementation does NOT replicate (see
    bm25.py's module docstring). So a term-frequency-only comparison is only
    guaranteed to match the third-party library when every query term's idf
    is positive under the classical formula, which is the regime exercised
    here (and the regime that matters for the real NFCorpus run -- rare,
    genuinely discriminating query terms).
    """

    def test_scores_match_rank_bm25_within_floating_point_tolerance(self):
        rank_bm25 = pytest.importorskip("rank_bm25")
        corpus = TestTermSaturationAndLengthNormalization._corpus()
        doc_ids = list(corpus)
        tokenized = [corpus[d].lower().split() for d in doc_ids]

        theirs = rank_bm25.BM25Okapi(tokenized, k1=1.2, b=0.75)
        ours = BM25Retriever(BM25Config(k1=1.2, b=0.75, top_k=len(doc_ids))).fit(corpus)

        query = "insulin therapy"
        query_tokens = query.lower().split()
        their_scores = theirs.get_scores(query_tokens)
        our_scores = dict(ours.rank(query, top_k=len(doc_ids)))

        for i, doc_id in enumerate(doc_ids):
            assert our_scores.get(doc_id, 0.0) == pytest.approx(their_scores[i], abs=1e-6)
