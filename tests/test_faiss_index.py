"""Tests for the FAISS dense-index wrapper (M3/M4).

Uses small hand-built vectors (no model loading, no network) so these run
fast and deterministically in CI.
"""

from __future__ import annotations

import numpy as np
import pytest

from biomedical_ir.faiss_index import FaissDenseIndex


class TestBuild:
    def test_build_sets_ntotal_and_dim(self):
        vecs = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]], dtype="float32")
        idx = FaissDenseIndex.build(["A", "B", "C"], vecs)
        assert idx.ntotal == 3
        assert idx.dim == 2

    def test_mismatched_lengths_raise(self):
        vecs = np.array([[1.0, 0.0], [0.0, 1.0]], dtype="float32")
        with pytest.raises(ValueError):
            FaissDenseIndex.build(["A"], vecs)

    def test_index_size_bytes_is_ntotal_times_dim_times_4(self):
        vecs = np.zeros((5, 8), dtype="float32")
        idx = FaissDenseIndex.build([str(i) for i in range(5)], vecs)
        assert idx.index_size_bytes() == 5 * 8 * 4


class TestSearch:
    def test_exact_nearest_neighbor_by_inner_product(self):
        # Normalized 2D vectors along cardinal directions; inner product with
        # a normalized query should rank the parallel vector first.
        doc_ids = ["north", "east", "diagonal"]
        vecs = np.array([[0.0, 1.0], [1.0, 0.0], [0.70710678, 0.70710678]], dtype="float32")
        idx = FaissDenseIndex.build(doc_ids, vecs)

        query = np.array([[0.0, 1.0]], dtype="float32")  # points exactly at "north"
        results = idx.search(query, top_k=3)
        assert results[0][0][0] == "north"
        assert results[0][0][1] == pytest.approx(1.0, abs=1e-5)

    def test_top_k_capped_at_corpus_size(self):
        vecs = np.eye(2, dtype="float32")
        idx = FaissDenseIndex.build(["A", "B"], vecs)
        results = idx.search(np.array([[1.0, 0.0]], dtype="float32"), top_k=100)
        assert len(results[0]) == 2  # never more results than documents indexed

    def test_multiple_queries_batched(self):
        vecs = np.array([[1.0, 0.0], [0.0, 1.0]], dtype="float32")
        idx = FaissDenseIndex.build(["A", "B"], vecs)
        queries = np.array([[1.0, 0.0], [0.0, 1.0]], dtype="float32")
        results = idx.search(queries, top_k=1)
        assert results[0][0][0] == "A"
        assert results[1][0][0] == "B"

    def test_1d_query_is_reshaped(self):
        vecs = np.array([[1.0, 0.0], [0.0, 1.0]], dtype="float32")
        idx = FaissDenseIndex.build(["A", "B"], vecs)
        results = idx.search(np.array([1.0, 0.0], dtype="float32"), top_k=1)
        assert len(results) == 1
        assert results[0][0][0] == "A"


class TestDenseModelConfig:
    def test_from_config_defaults(self):
        from biomedical_ir.dense import DenseModelConfig

        cfg = DenseModelConfig.from_config({})
        assert cfg.name == "BAAI/bge-base-en-v1.5"
        assert cfg.normalize_embeddings is True
        assert cfg.query_instruction.startswith("Represent this sentence")

    def test_from_config_overrides(self):
        from biomedical_ir.dense import DenseModelConfig

        cfg = DenseModelConfig.from_config(
            {
                "model": {"name": "some/other-model", "normalize_embeddings": False},
                "retrieval": {"top_k": 50},
                "device": {"batch_size": 16},
            }
        )
        assert cfg.name == "some/other-model"
        assert cfg.normalize_embeddings is False
        assert cfg.top_k == 50
        assert cfg.batch_size == 16
