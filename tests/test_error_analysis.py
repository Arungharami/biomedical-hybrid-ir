"""Tests for query-level diagnostic error analysis (M8, Section 17 of the spec)."""

from __future__ import annotations

from biomedical_ir.error_analysis import diagnose, diagnose_with_counts, get_rank


def make_run(qid_to_ranked_ids: dict[str, list[str]]):
    """Build a RunType from {qid: [doc_id_in_rank_order, ...]}, descending scores."""
    return {
        qid: [(d, float(len(ids) - i)) for i, d in enumerate(ids)]
        for qid, ids in qid_to_ranked_ids.items()
    }


CORPUS = {
    "D_bm25_win": {"title": "Lexical Match Doc", "text": "Exact keyword overlap with the query."},
    "D_medcpt_win": {"title": "Semantic Match Doc", "text": "Paraphrased content, no shared terms."},
    "D_filler": {"title": "Filler", "text": "Irrelevant filler document."},
}


class TestGetRank:
    def test_rank_found(self):
        run = make_run({"q1": ["A", "B", "C"]})
        assert get_rank(run, "q1", "B") == 2

    def test_rank_missing_returns_none(self):
        run = make_run({"q1": ["A", "B"]})
        assert get_rank(run, "q1", "Z") is None

    def test_unknown_query_returns_none(self):
        run = make_run({"q1": ["A"]})
        assert get_rank(run, "q2", "A") is None


class TestDiagnoseCategories:
    def test_bm25_wins_medcpt_loses(self):
        queries = {"q1": "keyword query"}
        qrels = {"q1": {"D_bm25_win": 1}}
        runs = {
            "bm25": make_run({"q1": ["D_bm25_win", "D_filler"]}),  # rank 1
            "medcpt": make_run({"q1": ["D_filler"]}),  # D_bm25_win absent -> rank None
        }
        result = diagnose(runs, queries, qrels, CORPUS, max_examples_per_category=5)
        assert len(result["bm25_wins_medcpt_loses"]) == 1
        ex = result["bm25_wins_medcpt_loses"][0]
        assert ex.doc_id == "D_bm25_win"
        assert ex.ranks["bm25"] == 1
        assert ex.ranks["medcpt"] is None
        assert ex.relevance == 1
        assert ex.query == "keyword query"

    def test_medcpt_wins_bm25_loses(self):
        queries = {"q1": "semantic query"}
        qrels = {"q1": {"D_medcpt_win": 2}}
        runs = {
            "bm25": make_run({"q1": ["D_filler"]}),
            "medcpt": make_run({"q1": ["D_medcpt_win", "D_filler"]}),
        }
        result = diagnose(runs, queries, qrels, CORPUS)
        assert len(result["medcpt_wins_bm25_loses"]) == 1
        assert result["medcpt_wins_bm25_loses"][0].doc_id == "D_medcpt_win"

    def test_hybrid_fixes_lexical_failure(self):
        queries = {"q1": "q"}
        qrels = {"q1": {"D_medcpt_win": 1}}
        runs = {
            "bm25": make_run({"q1": ["D_filler"]}),  # misses it (rank None, > BAD_RANK)
            "hybrid_rrf": make_run({"q1": ["D_medcpt_win", "D_filler"]}),  # rank 1
        }
        result = diagnose(runs, queries, qrels, CORPUS)
        assert len(result["hybrid_fixes_lexical_failure"]) == 1
        assert result["hybrid_fixes_lexical_failure"][0].doc_id == "D_medcpt_win"

    def test_hybrid_fixes_semantic_failure(self):
        queries = {"q1": "q"}
        qrels = {"q1": {"D_bm25_win": 1}}
        runs = {
            "medcpt": make_run({"q1": ["D_filler"]}),
            "hybrid_rrf": make_run({"q1": ["D_bm25_win", "D_filler"]}),
        }
        result = diagnose(runs, queries, qrels, CORPUS)
        assert len(result["hybrid_fixes_semantic_failure"]) == 1

    def test_reranker_improves_result(self):
        queries = {"q1": "q"}
        qrels = {"q1": {"D_bm25_win": 1}}
        runs = {
            "hybrid_rrf": make_run({"q1": ["D_filler", "D_bm25_win"]}),  # rank 2
            "hybrid_reranked": make_run({"q1": ["D_bm25_win", "D_filler"]}),  # rank 1
        }
        result = diagnose(runs, queries, qrels, CORPUS)
        assert len(result["reranker_improves_result"]) == 1
        assert result["reranker_improves_result"][0].ranks["hybrid_rrf"] == 2
        assert result["reranker_improves_result"][0].ranks["hybrid_reranked"] == 1

    def test_reranker_degrades_result(self):
        queries = {"q1": "q"}
        qrels = {"q1": {"D_bm25_win": 1}}
        runs = {
            "hybrid_rrf": make_run({"q1": ["D_bm25_win", "D_filler"]}),  # rank 1
            "hybrid_reranked": make_run({"q1": ["D_filler", "D_bm25_win"]}),  # rank 2
        }
        result = diagnose(runs, queries, qrels, CORPUS)
        assert len(result["reranker_degrades_result"]) == 1

    def test_non_relevant_docs_ignored(self):
        queries = {"q1": "q"}
        qrels = {"q1": {"D_filler": 0}}  # relevance 0 -> not a "relevant document"
        runs = {"bm25": make_run({"q1": ["D_filler"]}), "medcpt": make_run({"q1": []})}
        result = diagnose(runs, queries, qrels, CORPUS)
        assert all(len(v) == 0 for v in result.values())

    def test_doc_not_in_corpus_ignored(self):
        queries = {"q1": "q"}
        qrels = {"q1": {"D_unknown": 1}}
        runs = {"bm25": make_run({"q1": ["D_unknown"]}), "medcpt": make_run({"q1": []})}
        result = diagnose(runs, queries, qrels, CORPUS)
        assert all(len(v) == 0 for v in result.values())

    def test_max_examples_per_category_truncates(self):
        queries = {f"q{i}": "q" for i in range(10)}
        qrels = {f"q{i}": {"D_bm25_win": 1} for i in range(10)}
        runs = {
            "bm25": make_run({f"q{i}": ["D_bm25_win"] for i in range(10)}),
            "medcpt": make_run({f"q{i}": [] for i in range(10)}),
        }
        result = diagnose(runs, queries, qrels, CORPUS, max_examples_per_category=3)
        assert len(result["bm25_wins_medcpt_loses"]) == 3


class TestDiagnoseWithCounts:
    def test_counts_reflect_full_total_not_truncated(self):
        queries = {f"q{i}": "q" for i in range(10)}
        qrels = {f"q{i}": {"D_bm25_win": 1} for i in range(10)}
        runs = {
            "bm25": make_run({f"q{i}": ["D_bm25_win"] for i in range(10)}),
            "medcpt": make_run({f"q{i}": [] for i in range(10)}),
        }
        examples, counts = diagnose_with_counts(
            runs, queries, qrels, CORPUS, max_examples_per_category=3
        )
        assert len(examples["bm25_wins_medcpt_loses"]) == 3  # truncated for display
        assert counts["bm25_wins_medcpt_loses"] == 10  # but the true total is reported


class TestErrorExampleSnippet:
    def test_snippet_truncated_with_ellipsis(self):
        long_corpus = {"D1": {"title": "T", "text": "word " * 100}}
        queries = {"q1": "q"}
        qrels = {"q1": {"D1": 1}}
        runs = {"bm25": make_run({"q1": ["D1"]}), "medcpt": make_run({"q1": []})}
        result = diagnose(runs, queries, qrels, long_corpus)
        ex = result["bm25_wins_medcpt_loses"][0]
        assert ex.doc_snippet.endswith("...")
        assert len(ex.doc_snippet) <= 224
