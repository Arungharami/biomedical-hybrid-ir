import unittest

from biomedical_ir.evaluation import (
    mean_average_precision,
    mean_ndcg_at_k,
    mean_precision_at_k,
    mean_recall_at_k,
    mean_reciprocal_rank,
)


class TestMissingQueryRegressions(unittest.TestCase):
    def test_omitted_queries_count_as_zero_for_all_helpers(self):
        qrels = {"answered": {"d": 1}, "missing": {"d": 1}}
        run = {"answered": [("d", 1.0)], "unjudged": [("d", 2.0)]}
        for metric in (mean_precision_at_k, mean_recall_at_k, mean_reciprocal_rank,
                       mean_average_precision, mean_ndcg_at_k):
            with self.subTest(metric=metric.__name__):
                self.assertEqual(metric(run, qrels, 1), 0.5)
                self.assertEqual(metric({}, qrels, 1), 0.0)

    def test_explicit_empty_and_omitted_query_are_equivalent(self):
        qrels = {"q": {"d": 1}}
        self.assertEqual(mean_average_precision({}, qrels), mean_average_precision({"q": []}, qrels))
