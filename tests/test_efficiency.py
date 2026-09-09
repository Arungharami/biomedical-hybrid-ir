"""Tests for the effectiveness/efficiency table builder (M7, Section 19)."""

from __future__ import annotations

import json

from biomedical_ir.efficiency import build_efficiency_table


def write_metrics(tmp_path, name, payload):
    (tmp_path / f"{name}.json").write_text(json.dumps(payload))


class TestBuildEfficiencyTable:
    def test_missing_files_marked_missing(self, tmp_path):
        rows = build_efficiency_table(tmp_path)
        assert all(r["status"] == "missing" for r in rows)
        assert len(rows) == 6  # one per model in _MODEL_FILES

    def test_complete_row_extracted(self, tmp_path):
        write_metrics(
            tmp_path,
            "bge",
            {
                "device": "mps",
                "timing": {"latency_ms_per_query": 2.678},
                "index": {"embedding_dim": 768, "size_bytes": 11160576},
                "metrics": {"nDCG@10": 0.3712, "MAP": 0.1831, "Recall@100": 0.3368},
            },
        )
        rows = build_efficiency_table(tmp_path)
        bge_row = next(r for r in rows if r["model"] == "bge")
        assert bge_row["status"] == "complete"
        assert bge_row["device"] == "mps"
        assert bge_row["embedding_dim"] == 768
        assert bge_row["nDCG@10"] == 0.3712

    def test_model_without_device_field_defaults_to_cpu(self, tmp_path):
        write_metrics(
            tmp_path,
            "tfidf",
            {"timing": {"latency_ms_per_query": 3.631}, "metrics": {"nDCG@10": 0.305}},
        )
        rows = build_efficiency_table(tmp_path)
        tfidf_row = next(r for r in rows if r["model"] == "tfidf")
        assert tfidf_row["device"] == "cpu"
        assert tfidf_row["embedding_dim"] is None
