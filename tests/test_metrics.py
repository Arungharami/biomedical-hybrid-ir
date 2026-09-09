"""Tests for src/biomedical_ir/evaluation.py (Section 14 of the project spec):
custom educational metric implementations cross-checked against pytrec_eval,
plus the graded-relevance-handling investigation this module's conventions
are based on.
"""

from __future__ import annotations

import pytest
import pytrec_eval

from biomedical_ir.evaluation import (
    average_precision,
    evaluate_run,
    load_trec_run,
    mean_average_precision,
    mean_ndcg_at_k,
    mean_precision_at_k,
    mean_recall_at_k,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    save_run_json,
    save_trec_run,
)


def make_graded_run_and_qrels():
    """One query, 4 ranked docs, graded relevance {2, 1, 0, 1} in rank order."""
    qrels = {"q1": {"d1": 2, "d2": 1, "d3": 0, "d4": 1}}
    run = {"q1": [("d1", 4.0), ("d2", 3.0), ("d3", 2.0), ("d4", 1.0)]}
    return run, qrels


class TestGradedRelevanceHandling:
    """Documents the empirical investigation referenced in evaluation.py's
    module docstring: how pytrec_eval/trec_eval treats graded (0/1/2)
    relevance for binary-style measures vs. nDCG's gain function."""

    def test_binary_measures_treat_any_positive_grade_as_relevant(self):
        run, qrels = make_graded_run_and_qrels()
        # 3 relevant docs (d1 rel=2, d2 rel=1, d4 rel=1); d3 rel=0 not relevant.
        # AP = (P@1=1/1 + P@2=2/2 + P@4=3/4) / 3 = (1 + 1 + 0.75) / 3
        pytrec_ev = pytrec_eval.RelevanceEvaluator(
            {"q1": qrels["q1"]}, {"map", "recip_rank", "P.10", "recall.10"}
        )
        result = pytrec_ev.evaluate({"q1": {d: s for d, s in run["q1"]}})["q1"]
        assert result["map"] == pytest.approx((1 + 1 + 0.75) / 3, abs=1e-9)
        assert result["recip_rank"] == pytest.approx(1.0, abs=1e-9)  # d1 (rank 1) is relevant
        assert result["recall_10"] == pytest.approx(1.0, abs=1e-9)  # all 3 relevant retrieved

    def test_p_at_k_divides_by_k_not_by_num_retrieved(self):
        # Only 4 docs retrieved but P.10 still divides by 10 -> 3/10, not 3/4.
        run, qrels = make_graded_run_and_qrels()
        pytrec_ev = pytrec_eval.RelevanceEvaluator({"q1": qrels["q1"]}, {"P.10"})
        result = pytrec_ev.evaluate({"q1": {d: s for d, s in run["q1"]}})["q1"]
        assert result["P_10"] == pytest.approx(0.3, abs=1e-9)

    def test_ndcg_uses_linear_gain_not_exponential(self):
        # gain(rel) = rel (linear), NOT (2**rel - 1) (exponential/Burges).
        import math

        run, qrels = make_graded_run_and_qrels()
        pytrec_ev = pytrec_eval.RelevanceEvaluator({"q1": qrels["q1"]}, {"ndcg_cut.10"})
        result = pytrec_ev.evaluate({"q1": {d: s for d, s in run["q1"]}})["q1"]

        rels_in_rank_order = [2, 1, 0, 1]
        ideal = sorted(rels_in_rank_order, reverse=True)
        linear_dcg = sum(r / math.log2(i + 2) for i, r in enumerate(rels_in_rank_order))
        linear_idcg = sum(r / math.log2(i + 2) for i, r in enumerate(ideal))
        exp_dcg = sum((2**r - 1) / math.log2(i + 2) for i, r in enumerate(rels_in_rank_order))
        exp_idcg = sum((2**r - 1) / math.log2(i + 2) for i, r in enumerate(ideal))

        assert result["ndcg_cut_10"] == pytest.approx(linear_dcg / linear_idcg, abs=1e-9)
        assert result["ndcg_cut_10"] != pytest.approx(exp_dcg / exp_idcg, abs=1e-9)

    def test_zero_relevant_documents_gives_zero_not_nan(self):
        qrels = {"q1": {"d1": 0}}
        run = {"q1": {"d1": 4.0, "d2": 3.0}}
        pytrec_ev = pytrec_eval.RelevanceEvaluator(
            qrels, {"P.10", "recall.10", "map", "recip_rank", "ndcg_cut.10"}
        )
        result = pytrec_ev.evaluate(run)["q1"]
        assert all(v == 0.0 for v in result.values())

    def test_pytrec_eval_silently_ignores_run_queries_absent_from_qrels(self):
        qrels = {"q1": {"d1": 1}}
        run = {"q1": {"d1": 1.0}, "q2": {"d1": 1.0}}
        pytrec_ev = pytrec_eval.RelevanceEvaluator(qrels, {"map"})
        result = pytrec_ev.evaluate(run)
        assert set(result.keys()) == {"q1"}


class TestCustomMetricsMatchPytrecEval:
    """Cross-checks our from-scratch implementations against pytrec_eval on
    a small synthetic run + graded qrels; should match within float tolerance."""

    def _pytrec(self, measure, run, qrels):
        ev = pytrec_eval.RelevanceEvaluator(qrels, {measure})
        return ev.evaluate({qid: {d: s for d, s in docs} for qid, docs in run.items()})

    def test_precision_at_k_matches(self):
        run, qrels = make_graded_run_and_qrels()
        ranked_ids = [d for d, _ in run["q1"]]
        ours = precision_at_k(ranked_ids, qrels["q1"], 10)
        theirs = self._pytrec("P.10", run, qrels)["q1"]["P_10"]
        assert ours == pytest.approx(theirs, abs=1e-9)

    def test_recall_at_k_matches(self):
        run, qrels = make_graded_run_and_qrels()
        ranked_ids = [d for d, _ in run["q1"]]
        ours = recall_at_k(ranked_ids, qrels["q1"], 10)
        theirs = self._pytrec("recall.10", run, qrels)["q1"]["recall_10"]
        assert ours == pytest.approx(theirs, abs=1e-9)

    def test_reciprocal_rank_matches(self):
        run, qrels = make_graded_run_and_qrels()
        ranked_ids = [d for d, _ in run["q1"]]
        ours = reciprocal_rank(ranked_ids, qrels["q1"])
        theirs = self._pytrec("recip_rank", run, qrels)["q1"]["recip_rank"]
        assert ours == pytest.approx(theirs, abs=1e-9)

    def test_average_precision_matches_map(self):
        run, qrels = make_graded_run_and_qrels()
        ranked_ids = [d for d, _ in run["q1"]]
        ours = average_precision(ranked_ids, qrels["q1"])
        theirs = self._pytrec("map", run, qrels)["q1"]["map"]
        assert ours == pytest.approx(theirs, abs=1e-9)

    def test_ndcg_at_k_matches(self):
        run, qrels = make_graded_run_and_qrels()
        ranked_ids = [d for d, _ in run["q1"]]
        ours = ndcg_at_k(ranked_ids, qrels["q1"], 10)
        theirs = self._pytrec("ndcg_cut.10", run, qrels)["q1"]["ndcg_cut_10"]
        assert ours == pytest.approx(theirs, abs=1e-9)

    def test_multi_query_run_matches_on_every_measure(self):
        # A slightly larger synthetic run/qrels with 3 queries of varying
        # difficulty (including one with zero relevant docs).
        qrels = {
            "q1": {"d1": 2, "d2": 0, "d3": 1},
            "q2": {"d5": 1, "d6": 1},
            "q3": {"d9": 0},
        }
        run = {
            "q1": [("d1", 3.0), ("d2", 2.0), ("d3", 1.0)],
            "q2": [("d7", 3.0), ("d6", 2.0), ("d5", 1.0)],
            "q3": [("d9", 1.0), ("d10", 0.5)],
        }
        results = evaluate_run(run, qrels, include_per_query=True)
        per_query = results["per_query"]

        for qid, docs in run.items():
            ranked_ids = [d for d, _ in docs]
            q_qrels = qrels[qid]
            assert precision_at_k(ranked_ids, q_qrels, 10) == pytest.approx(
                per_query[qid]["P_10"], abs=1e-9
            )
            assert recall_at_k(ranked_ids, q_qrels, 10) == pytest.approx(
                per_query[qid]["recall_10"], abs=1e-9
            )
            assert reciprocal_rank(ranked_ids, q_qrels) == pytest.approx(
                per_query[qid]["recip_rank"], abs=1e-9
            )
            assert average_precision(ranked_ids, q_qrels) == pytest.approx(
                per_query[qid]["map"], abs=1e-9
            )
            assert ndcg_at_k(ranked_ids, q_qrels, 10) == pytest.approx(
                per_query[qid]["ndcg_cut_10"], abs=1e-9
            )

    def test_mean_wrappers_match_evaluate_run_summary(self):
        qrels = {
            "q1": {"d1": 2, "d2": 0, "d3": 1},
            "q2": {"d5": 1, "d6": 1},
        }
        run = {
            "q1": [("d1", 3.0), ("d2", 2.0), ("d3", 1.0)],
            "q2": [("d7", 3.0), ("d6", 2.0), ("d5", 1.0)],
        }
        results = evaluate_run(run, qrels)["summary"]
        assert mean_precision_at_k(run, qrels, 10) == pytest.approx(results["P@10"], abs=1e-9)
        assert mean_recall_at_k(run, qrels, 10) == pytest.approx(results["Recall@10"], abs=1e-9)
        assert mean_reciprocal_rank(run, qrels) == pytest.approx(results["MRR"], abs=1e-9)
        assert mean_average_precision(run, qrels) == pytest.approx(results["MAP"], abs=1e-9)
        assert mean_ndcg_at_k(run, qrels, 10) == pytest.approx(results["nDCG@10"], abs=1e-9)


class TestEdgeCases:
    def test_zero_relevant_documents_all_custom_metrics_are_zero(self):
        qrels = {"d1": 0, "d2": 0}
        ranked = ["d1", "d2"]
        assert precision_at_k(ranked, qrels, 10) == 0.0
        assert recall_at_k(ranked, qrels, 10) == 0.0
        assert reciprocal_rank(ranked, qrels) == 0.0
        assert average_precision(ranked, qrels) == 0.0
        assert ndcg_at_k(ranked, qrels, 10) == 0.0

    def test_empty_ranked_list_does_not_raise(self):
        qrels = {"d1": 1}
        assert precision_at_k([], qrels, 10) == 0.0
        assert recall_at_k([], qrels, 10) == 0.0
        assert reciprocal_rank([], qrels) == 0.0
        assert ndcg_at_k([], qrels, 10) == 0.0

    def test_k_must_be_positive(self):
        qrels = {"d1": 1}
        with pytest.raises(ValueError):
            precision_at_k(["d1"], qrels, 0)
        with pytest.raises(ValueError):
            recall_at_k(["d1"], qrels, -1)
        with pytest.raises(ValueError):
            ndcg_at_k(["d1"], qrels, 0)

    def test_malformed_run_missing_doc_in_qrels_treated_as_not_relevant(self):
        qrels = {"d1": 1}
        ranked = ["d1", "d_not_in_qrels"]
        # A doc absent from qrels is simply treated as non-relevant, not an error.
        assert precision_at_k(ranked, qrels, 2) == 0.5

    def test_evaluate_run_drops_queries_not_in_qrels(self):
        qrels = {"q1": {"d1": 1}}
        run = {"q1": [("d1", 1.0)], "q2": [("d1", 1.0)]}
        results = evaluate_run(run, qrels)
        assert results["num_queries_evaluated"] == 1
        assert results["dropped_queries_not_in_qrels"] == ["q2"]


class TestTrecRunIO:
    def test_save_and_load_trec_run_roundtrip(self, tmp_path):
        run = {"q1": [("d1", 3.0), ("d2", 1.5)], "q2": [("d3", 0.9)]}
        path = save_trec_run(run, tmp_path / "test.trec", run_tag="testrun")
        assert path.exists()
        loaded = load_trec_run(path)
        assert set(loaded.keys()) == {"q1", "q2"}
        assert loaded["q1"][0][0] == "d1"
        assert loaded["q1"][0][1] == pytest.approx(3.0)

    def test_trec_format_has_six_columns(self, tmp_path):
        run = {"q1": [("d1", 3.0)]}
        path = save_trec_run(run, tmp_path / "test.trec", run_tag="testrun")
        line = path.read_text().strip().splitlines()[0]
        parts = line.split()
        assert len(parts) == 6
        assert parts[0] == "q1"
        assert parts[1] == "Q0"
        assert parts[2] == "d1"
        assert parts[3] == "1"
        assert parts[5] == "testrun"

    def test_save_run_json_roundtrip(self, tmp_path):
        import json

        run = {"q1": [("d1", 3.0), ("d2", 1.5)]}
        path = save_run_json(run, tmp_path / "run.json")
        reloaded = json.loads(path.read_text())
        assert reloaded["q1"][0] == ["d1", 3.0]
