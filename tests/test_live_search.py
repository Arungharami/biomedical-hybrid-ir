"""Tests for the live demo engine (biomedical_ir/live_search.py).

Dense retriever and cross-encoder are replaced by tiny deterministic stand-ins
so these tests need no model weights; the BM25 index, RRF, and metric code
under test are the real library implementations.
"""

from __future__ import annotations

import math

import pytest

from biomedical_ir.bm25 import BM25Retriever
from biomedical_ir.data import compose_document_text
from biomedical_ir.fusion import reciprocal_rank_fusion
from biomedical_ir.live_search import (
    BM25,
    HYBRID,
    MEDCPT,
    RERANK,
    LiveSearchEngine,
    judge_ranking,
)

CORPUS = {
    "D1": {"title": "Salmon and omega-3", "text": "Farmed salmon contains omega-3 fatty acids."},
    "D2": {"title": "Alendronate and bone", "text": "Bisphosphonates reduce fracture risk in osteoporosis."},
    "D3": {"title": "Green tea", "text": "Green tea catechins and LDL cholesterol."},
    "D4": {"title": "Fish oil", "text": "Fish oil supplements and heart disease."},
}


class FixedDense:
    """Stand-in dense retriever: always returns a fixed order (D2, D4, D1, D3)."""

    calls = 0

    def rank_all(self, queries, top_k=None):
        FixedDense.calls += 1
        order = [("D2", 0.9), ("D4", 0.8), ("D1", 0.7), ("D3", 0.6)]
        return {qid: order[:top_k] for qid in queries}


class ReverseReranker:
    """Stand-in cross-encoder: reverses the candidate order it is given."""

    def __init__(self):
        self.seen = None

    def rerank_query(self, query, candidates, corpus, top_k=None):
        self.seen = [d for d, _ in candidates]
        rev = list(reversed(self.seen))
        return [(d, float(len(rev) - i)) for i, d in enumerate(rev)][:top_k]


@pytest.fixture
def engine():
    FixedDense.calls = 0
    rr = ReverseReranker()
    eng = LiveSearchEngine(CORPUS, dense_factory=FixedDense, reranker_factory=lambda: rr)
    eng._test_reranker = rr
    return eng


def test_bm25_mode_matches_library_bm25(engine):
    ref = BM25Retriever().fit(
        {d: compose_document_text(m["title"], m["text"]) for d, m in CORPUS.items()}
    ).rank("salmon omega-3", top_k=100)
    res = engine.search("salmon omega-3", BM25, top_k=10)
    assert [(h.doc_id, pytest.approx(h.score)) for h in res.hits] == [(d, pytest.approx(s)) for d, s in ref]
    assert FixedDense.calls == 0, "BM25 mode must not load the dense model"


def test_hybrid_mode_is_rrf_of_both_rankings(engine):
    bm25_ids = [d for d, _ in engine.bm25_ranking("salmon fish oil")]
    expected = reciprocal_rank_fusion([bm25_ids, ["D2", "D4", "D1", "D3"]], k=60)
    res = engine.search("salmon fish oil", HYBRID, top_k=10)
    assert [h.doc_id for h in res.hits] == [d for d, _ in expected]
    for h, (d, s) in zip(res.hits, expected):
        assert h.score == pytest.approx(s)
        # component ranks are exposed so the demo can explain fusion
        assert h.dense_rank == ["D2", "D4", "D1", "D3"].index(d) + 1


def test_rrf_score_hand_computed(engine):
    res = engine.search("salmon", HYBRID, top_k=10)
    d1 = next(h for h in res.hits if h.doc_id == "D1")
    # D1 is BM25 rank 1 and dense rank 3
    assert d1.bm25_rank == 1 and d1.dense_rank == 3
    assert d1.score == pytest.approx(1 / 61 + 1 / 63)


def test_vocabulary_mismatch_falls_back_to_dense(engine):
    res = engine.search("Fosamax", HYBRID, top_k=10)
    assert engine.bm25_ranking("Fosamax") == []
    assert [h.doc_id for h in res.hits] == ["D2", "D4", "D1", "D3"]
    assert any("vocabulary mismatch" in n for n in res.notes)
    assert engine.search("Fosamax", BM25).hits == []


def test_rerank_only_reorders_the_candidate_pool(engine):
    hybrid = [h.doc_id for h in engine.search("salmon fish oil", HYBRID, top_k=10).hits]
    res = engine.search("salmon fish oil", RERANK, top_k=10, pool=2)
    assert engine._test_reranker.seen == hybrid[:2]
    assert [h.doc_id for h in res.hits] == list(reversed(hybrid[:2]))
    assert [h.rrf_rank for h in res.hits] == [2, 1]


def test_dense_mode_and_lazy_loading(engine):
    assert FixedDense.calls == 0
    res = engine.search("anything", MEDCPT, top_k=2)
    assert [h.doc_id for h in res.hits] == ["D2", "D4"]
    assert res.latency_ms >= 0


def test_bad_inputs(engine):
    with pytest.raises(ValueError):
        engine.search("x", "Google")
    assert engine.search("   ", HYBRID).hits == []
    no_models = LiveSearchEngine(CORPUS)
    with pytest.raises(RuntimeError):
        no_models.search("salmon", MEDCPT)


def test_judge_ranking_hand_computed():
    qrels = {"A": 2, "B": 1, "C": 1, "Z": 0}
    scores = judge_ranking(["X", "A", "Y", "C"], qrels, k=10)
    assert scores["P@10"] == pytest.approx(2 / 10)
    assert scores["RR@10"] == pytest.approx(1 / 2)
    dcg = 2 / math.log2(3) + 1 / math.log2(5)
    idcg = 2 / math.log2(2) + 1 / math.log2(3) + 1 / math.log2(4)
    assert scores["nDCG@10"] == pytest.approx(dcg / idcg)
    assert scores["judged_relevant"] == 3
