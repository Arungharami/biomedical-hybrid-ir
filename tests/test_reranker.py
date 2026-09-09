"""Tests for cross-encoder reranker config parsing and article formatting (M6).

No network calls / model loading here (kept fast and network-independent
for CI) -- the actual cross-encoder is exercised for real by
``scripts/run_reranker.py`` and validated against genuine NFCorpus results
in ``results/metrics/hybrid_reranked.json``.
"""

from __future__ import annotations

from biomedical_ir.reranker import RerankerConfig, format_article


class TestFormatArticle:
    def test_title_and_text_joined_with_period(self):
        out = format_article("Statins and Cancer", "Statins may reduce cancer risk.")
        assert out == "Statins and Cancer. Statins may reduce cancer risk."

    def test_title_only(self):
        assert format_article("Title only", "") == "Title only"

    def test_text_only(self):
        assert format_article("", "Body text only.") == "Body text only."

    def test_both_empty(self):
        assert format_article("", "") == ""

    def test_whitespace_stripped(self):
        out = format_article("  Title  ", "  Body  ")
        assert out == "Title. Body"

    def test_custom_template(self):
        out = format_article("T", "B", template="{title} -- {text}")
        assert out == "T -- B"


class TestRerankerConfig:
    def test_defaults_match_official_model_card(self):
        cfg = RerankerConfig.from_config({})
        assert cfg.model == "ncbi/MedCPT-Cross-Encoder"
        assert cfg.max_length == 512
        assert cfg.candidate_pool == 50  # configs/reranker.yaml default_candidate_pool

    def test_overrides_applied(self):
        cfg = RerankerConfig.from_config(
            {
                "reranker": {"default_candidate_pool": 20, "max_length": 256},
                "retrieval": {"top_k": 30},
                "device": {"batch_size": 8},
            }
        )
        assert cfg.candidate_pool == 20
        assert cfg.max_length == 256
        assert cfg.top_k == 30
        assert cfg.batch_size == 8
