"""Offline tests: real lexical models, synthetic judgments, mocked dense inference."""

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from biomedical_ir.evaluation import ndcg_at_k
from biomedical_ir.research_data import define_tuning_split, normalize_benchmark
from biomedical_ir.research_fusion import combine, validate_run, weighted_fusion
from biomedical_ir.research_pipeline import choose, query_conditions, run_study
from biomedical_ir.research_stats import comparison_report, holm_adjust, paired_effect
from scripts.summarize_research import aggregate


def fixture():
    corpus = [{"_id": str(i), "title": "", "text": text} for i, text in enumerate([
        "cardiac heart treatment", "lung respiratory infection", "diabetes glucose insulin",
        "kidney renal dialysis", "nutrition diet vitamin", "cancer tumor oncology"])]
    queries = [{"_id": str(i), "text": text} for i, text in enumerate([
        "cardiac", "lung", "diabetes", "renal", "vitamin", "oncology"])]
    qrels = {"train": [{"query-id": 0, "corpus-id": 0, "score": 1},
                         {"query-id": 1, "corpus-id": 1, "score": 1}],
             "validation": [{"query-id": 2, "corpus-id": 2, "score": 1},
                            {"query-id": 3, "corpus-id": 3, "score": 1}],
             "test": [{"query-id": 4, "corpus-id": 4, "score": 1},
                      {"query-id": 5, "corpus-id": 5, "score": 1}]}
    return corpus, queries, qrels


def educational_evaluator(run, qrels, include_per_query=False):
    per = {q: {"ndcg_cut_10": ndcg_at_k([d for d, _ in run.get(q, [])], docs, 10)}
           for q, docs in qrels.items()}
    result = {"summary": {"nDCG@10": sum(v["ndcg_cut_10"] for v in per.values()) / len(per)}}
    if include_per_query:
        result["per_query"] = per
    return result


def synthetic_dense(name, data, partitions, depth, provenance, device):
    # Explicit deterministic fixture, never an experimental model output.
    run = {s: {q: [(d, float(10 - i)) for i, d in enumerate(reversed(sorted(data.corpus)))]
               for q in queries} for s, queries in partitions.items()}
    provenance[name] = "synthetic-fixture"
    return run, {"synthetic": True}


class TestDataContracts(unittest.TestCase):
    def test_normalizes_numeric_ids_and_validation_name(self):
        data = normalize_benchmark(*fixture())
        self.assertEqual(data.qrels["dev"]["2"], {"2": 1})
        self.assertEqual(len(data.corpus), 6)

    def test_duplicate_documents_fail(self):
        c, q, r = fixture()
        with self.assertRaises(ValueError):
            normalize_benchmark(c + c[:1], q, r)

    def test_dangling_judgments_fail(self):
        c, q, r = fixture()
        r["test"][0]["corpus-id"] = 99
        with self.assertRaises(ValueError):
            normalize_benchmark(c, q, r)

    def test_split_id_overlap_fails(self):
        c, q, r = fixture()
        r["test"][0]["query-id"] = 0
        with self.assertRaises(ValueError):
            normalize_benchmark(c, q, r)

    def test_noninteger_relevance_fails(self):
        c, q, r = fixture()
        r["test"][0]["score"] = 0.5
        with self.assertRaises(ValueError):
            normalize_benchmark(c, q, r)

    def test_train_holdout_does_not_touch_test(self):
        c, q, r = fixture()
        del r["validation"]
        a = define_tuning_split(normalize_benchmark(c, q, r))
        b = define_tuning_split(normalize_benchmark(c, q, r))
        self.assertEqual(a.qrels, b.qrels)
        self.assertEqual(set(a.qrels["test"]), {"4", "5"})
        self.assertFalse(set(a.qrels["train"]) & set(a.qrels["dev"]))

    def test_test_only_has_no_created_dev(self):
        c, q, r = fixture()
        data = define_tuning_split(normalize_benchmark(c, q, {"test": r["test"]}))
        self.assertNotIn("dev", data.qrels)

    def test_dev_test_normalized_text_overlap_fails(self):
        c, q, r = fixture()
        q[4]["text"] = " DIABETES "
        with self.assertRaises(ValueError):
            define_tuning_split(normalize_benchmark(c, q, r))


class TestFusionContracts(unittest.TestCase):
    def test_weight_endpoints_preserve_active_ranking(self):
        a, b = {"q": [("a", 10), ("b", 1)]}, {"q": [("c", 2), ("a", 1)]}
        self.assertEqual(weighted_fusion(a, b, 1), a)
        self.assertEqual(weighted_fusion(a, b, 0), b)

    def test_minmax_handles_negative_and_equal_scores(self):
        a, b = {"q": [("a", -1), ("b", -2)]}, {"q": [("b", 5), ("c", 5)]}
        fused = dict(weighted_fusion(a, b)["q"])
        self.assertEqual(fused, {"a": 0.5, "b": 0.5, "c": 0.5})

    def test_depth_truncates_both_sources(self):
        a, b = {"q": [("a", 2), ("b", 1)]}, {"q": [("c", 2), ("d", 1)]}
        self.assertEqual(len(combine(a, b, "rrf", 60, depth=1)["q"]), 1)

    def test_duplicate_and_nonfinite_scores_fail(self):
        for run in [{"q": [("a", 2), ("a", 1)]}, {"q": [("a", float("nan"))]}]:
            with self.assertRaises(ValueError):
                validate_run(run, ["q"], ["a"])

    def test_missing_query_cannot_shrink_population(self):
        with self.assertRaises(ValueError):
            validate_run({"q": []}, ["q", "r"], ["a"])


class TestStatisticsContracts(unittest.TestCase):
    def test_holm_known_family(self):
        actual = holm_adjust([0.01, 0.04, 0.03])
        for observed, expected in zip(actual, [0.03, 0.06, 0.06]):
            self.assertAlmostEqual(observed, expected)

    def test_zero_effect_has_unit_p_and_zero_interval(self):
        effect = paired_effect([0, 1], [0, 1], resamples=100)
        self.assertEqual(effect["p_value"], 1)
        self.assertEqual(effect["ci95_low"], 0)
        self.assertEqual(effect["ci95_high"], 0)

    def test_effect_reproducible_and_directional(self):
        a = paired_effect([1] * 12, [0] * 12, resamples=500)
        self.assertEqual(a, paired_effect([1] * 12, [0] * 12, resamples=500))
        self.assertEqual(a["mean_difference"], 1)
        self.assertGreater(a["p_value"], 0)
        self.assertLess(a["p_value"], 0.05)

    def test_alignment_mismatch_fails(self):
        with self.assertRaises(ValueError):
            comparison_report({"a": {"q": 1}, "b": {"r": 1}}, [("a", "b")], 100)


class TestResearchPipeline(unittest.TestCase):
    def test_selection_uses_dev_score_and_deterministic_ties(self):
        data = normalize_benchmark(*fixture())
        trials = [("bad", {"2": [("0", 1)], "3": []}),
                  ("good", {"2": [("2", 1)], "3": [("3", 1)]})]
        selected, trace = choose(trials, data.qrels["dev"], educational_evaluator)
        self.assertEqual(selected, "good")
        self.assertEqual(len(trace), 2)

    def test_full_offline_orchestration_and_frozen_transfer(self):
        config = json.loads((Path(__file__).parents[1] / "configs/research.json").read_text())
        config["resamples"] = 100
        data = define_tuning_split(normalize_benchmark(*fixture()))
        data.provenance["dataset"] = "synthetic-fixture"
        with tempfile.TemporaryDirectory() as path:
            report = run_study(data, config, path, evaluator=educational_evaluator,
                               dense_provider=synthetic_dense)
            self.assertEqual(len(report["metrics"]), 8)
            self.assertEqual(report["statistics"]["family_size"], 8)
            selection = json.loads((Path(path) / "selection.json").read_text())
            self.assertEqual(len(selection["dev_trials"]["bm25"]), 9)
            frozen = selection["settings"]
            test_only = copy.deepcopy(data)
            test_only.qrels = {"test": data.qrels["test"]}
            with self.assertRaises(ValueError):
                run_study(test_only, config, Path(path) / "no-dev")
            transferred = run_study(test_only, config, Path(path) / "transfer", frozen=frozen,
                                    evaluator=educational_evaluator, dense_provider=synthetic_dense)
            self.assertEqual(report["metrics"], transferred["metrics"])

    def test_subgroups_are_descriptive_and_exhaustive_within_axis(self):
        report = query_conditions({"q": "short", "r": "one two three four five six seven eight nine"},
            {"q": [("a", 1)], "r": [("a", 1)]},
            {"q": [("b", 1)], "r": [("a", 1)]}, {"q": 0.1, "r": -0.1})
        self.assertEqual(report["short_le8_tokens"]["wins"], 1)
        self.assertEqual(report["long_gt8_tokens"]["losses"], 1)
        self.assertEqual(report["low_top10_overlap_le0.2"]["queries"], 1)

    def test_common_reranker_pool_and_all_candidate_sources(self):
        config = json.loads((Path(__file__).parents[1] / "configs/research.json").read_text())
        config.update(rerank=True, resamples=100)
        data = define_tuning_split(normalize_benchmark(*fixture()))
        calls = []

        class FakeReranker:
            def __init__(self, config, device):
                pass

            def rerank_run(self, run, queries, corpus, candidate_pool, top_k):
                calls.append(candidate_pool)
                return {q: ranking[:candidate_pool] for q, ranking in run.items()}

        with tempfile.TemporaryDirectory() as path:
            with patch("biomedical_ir.reranker.CrossEncoderReranker", FakeReranker), \
                 patch("biomedical_ir.research_pipeline.pinned_model", return_value="fixture"):
                report = run_study(data, config, path, evaluator=educational_evaluator,
                                   dense_provider=synthetic_dense)
            self.assertEqual(len(report["metrics"]), 15)
            self.assertEqual(report["statistics"]["family_size"], 15)
            selected = json.loads((Path(path) / "selection.json").read_text())["settings"]
            self.assertEqual(calls[-7:], [selected["rerank_pool"]] * 7)

    def test_notebook_json_and_code_compile(self):
        notebook = Path(__file__).parents[1] / "notebooks/Kaggle_MultiBenchmark_Research.ipynb"
        nb = json.loads(notebook.read_text())
        self.assertEqual(nb["nbformat"], 4)
        for cell in nb["cells"]:
            if cell["cell_type"] == "code":
                compile(cell["source"], str(notebook), "exec")


class TestStudyAggregation(unittest.TestCase):
    def write_run(self, root, dataset, status="complete", model_sha="fixture"):
        path = Path(root) / dataset
        path.mkdir()
        manifest = {"status": status, "dataset": dataset, "config": {
            "candidate_depth": 100, "dense_methods": ["bge", "medcpt"], "rerank": False}}
        report = {"model_shas": {"bge": model_sha}, "metrics": {"bm25": {"summary": {}}},
                  "primary_mean_ci95": {}, "statistics": {"comparisons": [{"p_value": 0.03}]}}
        (path / "manifest.json").write_text(json.dumps(manifest))
        (path / "report.json").write_text(json.dumps(report))
        return path

    def test_global_family_changes_rejection(self):
        with tempfile.TemporaryDirectory() as root:
            report = aggregate([self.write_run(root, "nfcorpus"), self.write_run(root, "scifact")])
            self.assertEqual(report["study_family_size"], 2)
            self.assertAlmostEqual(report["comparisons"][0]["p_holm_study"], 0.06)
            self.assertFalse(report["comparisons"][0]["reject_study_at_05"])

    def test_failed_run_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                aggregate([self.write_run(root, "nfcorpus", status="failed")])

    def test_model_version_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            paths = [self.write_run(root, "nfcorpus"), self.write_run(root, "scifact", model_sha="other")]
            with self.assertRaises(ValueError):
                aggregate(paths)

    def test_duplicate_dataset_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path = self.write_run(root, "nfcorpus")
            with self.assertRaises(ValueError):
                aggregate([path, path])


if __name__ == "__main__":
    unittest.main()
