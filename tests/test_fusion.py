"""Tests for Reciprocal Rank Fusion (M5, Section 10 of the project spec:
"Unit-test RRF using hand-created rankings.")
"""

from __future__ import annotations

import pytest

from biomedical_ir.fusion import RRFConfig, fuse_runs, reciprocal_rank_fusion


class TestReciprocalRankFusionHandComputed:
    """Two hand-created rankings:

        ranking1 = [A, B, C]   (A rank 1, B rank 2, C rank 3)
        ranking2 = [B, A, D]   (B rank 1, A rank 2, D rank 3)

    With k=1:
        RRF(A) = 1/(1+1) + 1/(1+2) = 0.5      + 0.333333... = 0.833333...
        RRF(B) = 1/(1+2) + 1/(1+1) = 0.333333... + 0.5      = 0.833333...
        RRF(C) = 1/(1+3) + 0                  = 0.25
        RRF(D) = 0        + 1/(1+3)           = 0.25
    A and B tie (symmetric under swapping which ranking each leads), as do C and D;
    ties are broken by ascending doc_id.
    """

    def test_scores_match_hand_computation_k1(self):
        result = reciprocal_rank_fusion([["A", "B", "C"], ["B", "A", "D"]], k=1)
        scores = dict(result)
        assert scores["A"] == pytest.approx(0.5 + 1 / 3)
        assert scores["B"] == pytest.approx(1 / 3 + 0.5)
        assert scores["C"] == pytest.approx(0.25)
        assert scores["D"] == pytest.approx(0.25)

    def test_ranking_order_with_tie_breaking_k1(self):
        result = reciprocal_rank_fusion([["A", "B", "C"], ["B", "A", "D"]], k=1)
        ordered_ids = [doc_id for doc_id, _ in result]
        # A and B tie on score -> ascending doc_id -> A before B.
        # C and D tie on score -> ascending doc_id -> C before D.
        assert ordered_ids == ["A", "B", "C", "D"]

    def test_default_k60_same_qualitative_ordering(self):
        result = reciprocal_rank_fusion([["A", "B", "C"], ["B", "A", "D"]], k=60)
        scores = dict(result)
        assert scores["A"] == pytest.approx(1 / 61 + 1 / 62)
        assert scores["B"] == pytest.approx(1 / 62 + 1 / 61)
        assert scores["A"] == pytest.approx(scores["B"])
        assert scores["C"] == pytest.approx(1 / 63)
        assert scores["D"] == pytest.approx(1 / 63)


class TestReciprocalRankFusionEdgeCases:
    def test_single_ranking_is_unchanged_in_relative_order(self):
        result = reciprocal_rank_fusion([["X", "Y", "Z"]], k=60)
        assert [d for d, _ in result] == ["X", "Y", "Z"]

    def test_document_only_in_one_ranking_still_included(self):
        result = reciprocal_rank_fusion([["A"], ["B", "C"]], k=60)
        ids = {d for d, _ in result}
        assert ids == {"A", "B", "C"}

    def test_empty_rankings_produce_empty_result(self):
        assert reciprocal_rank_fusion([[], []], k=60) == []

    def test_nonpositive_k_raises(self):
        with pytest.raises(ValueError):
            reciprocal_rank_fusion([["A"]], k=0)

    def test_agreement_boosts_rank_above_either_alone(self):
        # A document ranked #2 by both retrievers should outscore a document
        # ranked #1 by only one of them, once combined -- this is RRF's core
        # "agreement matters" property (Cormack, Clarke & Buettcher, 2009).
        ranking1 = ["solo_winner", "agreed_doc", "other"]
        ranking2 = ["agreed_doc", "unique_to_2", "other2"]
        result = dict(reciprocal_rank_fusion([ranking1, ranking2], k=60))
        assert result["agreed_doc"] > result["solo_winner"]


class TestFuseRuns:
    def test_fuses_two_component_runs(self):
        bm25_run = {"q1": [("A", 10.0), ("B", 8.0), ("C", 5.0)]}
        medcpt_run = {"q1": [("B", 0.9), ("A", 0.8), ("D", 0.5)]}
        fused = fuse_runs([bm25_run, medcpt_run], k=1, candidate_depth=100, top_k=100)
        ordered_ids = [d for d, _ in fused["q1"]]
        assert ordered_ids == ["A", "B", "C", "D"]  # matches the hand-computed case above

    def test_query_missing_from_one_component_still_appears(self):
        bm25_run = {"q1": [("A", 10.0)], "q2": [("B", 5.0)]}
        medcpt_run = {"q1": [("A", 0.9)]}  # q2 absent from medcpt_run entirely
        fused = fuse_runs([bm25_run, medcpt_run], k=60)
        assert "q2" in fused
        assert fused["q2"][0][0] == "B"

    def test_candidate_depth_truncates_before_fusion(self):
        bm25_run = {"q1": [("A", 10.0), ("B", 9.0), ("C", 8.0)]}
        medcpt_run = {"q1": [("C", 0.9)]}
        # candidate_depth=2 -> bm25's "C" (rank 3) is excluded from fusion input
        fused = fuse_runs([bm25_run, medcpt_run], k=60, candidate_depth=2, top_k=100)
        ids = {d for d, _ in fused["q1"]}
        # C still appears (contributed by medcpt_run), but only with medcpt's contribution
        assert "C" in ids
        c_score = dict(fused["q1"])["C"]
        assert c_score == pytest.approx(1 / 61)  # only medcpt's rank-1 contribution, not bm25's

    def test_top_k_truncates_output(self):
        bm25_run = {"q1": [(f"D{i}", float(100 - i)) for i in range(10)]}
        medcpt_run = {"q1": []}
        fused = fuse_runs([bm25_run, medcpt_run], k=60, candidate_depth=100, top_k=3)
        assert len(fused["q1"]) == 3

    def test_nonpositive_k_raises(self):
        with pytest.raises(ValueError):
            fuse_runs([{"q1": []}], k=0)


class TestRRFConfig:
    def test_defaults(self):
        cfg = RRFConfig.from_config({})
        assert cfg.k == 60
        assert cfg.candidate_depth == 100
        assert cfg.top_k == 100

    def test_overrides(self):
        cfg = RRFConfig.from_config(
            {"fusion": {"k": 30}, "retrieval": {"candidate_depth": 50, "top_k": 20}}
        )
        assert cfg.k == 30
        assert cfg.candidate_depth == 50
        assert cfg.top_k == 20
