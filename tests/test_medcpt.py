"""Tests for MedCPT config parsing (M4).

No network calls / model loading here (that would make CI slow and
network-dependent) -- the actual encoders are exercised for real by
``scripts/run_medcpt.py`` and validated against genuine NFCorpus results in
``results/metrics/medcpt.json``. Index search correctness is already covered
generically by ``tests/test_faiss_index.py`` (MedCPT reuses
:class:`biomedical_ir.faiss_index.FaissDenseIndex` unmodified).
"""

from __future__ import annotations

from biomedical_ir.medcpt import MedCPTConfig


class TestMedCPTConfig:
    def test_defaults_match_official_model_cards(self):
        cfg = MedCPTConfig.from_config({})
        assert cfg.query_encoder == "ncbi/MedCPT-Query-Encoder"
        assert cfg.article_encoder == "ncbi/MedCPT-Article-Encoder"
        assert cfg.query_max_length == 64
        assert cfg.article_max_length == 512

    def test_overrides_applied(self):
        cfg = MedCPTConfig.from_config(
            {
                "model": {"query_max_length": 32, "article_max_length": 256},
                "retrieval": {"top_k": 50},
                "device": {"batch_size": 8},
            }
        )
        assert cfg.query_max_length == 32
        assert cfg.article_max_length == 256
        assert cfg.top_k == 50
        assert cfg.batch_size == 8

    def test_top_k_default_is_100(self):
        cfg = MedCPTConfig.from_config({})
        assert cfg.top_k == 100
