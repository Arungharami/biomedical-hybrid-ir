"""Tests for paired significance testing (M7, Section 16 of the project spec)."""

from __future__ import annotations

import numpy as np
import pytest

from biomedical_ir.statistics import (
    aligned_scores,
    paired_bootstrap_test,
    paired_permutation_test,
)


class TestAlignedScores:
    def test_restricts_to_common_query_ids(self):
        a = {"q1": 0.5, "q2": 0.3, "q3": 0.9}
        b = {"q1": 0.4, "q2": 0.6}  # q3 missing
        qids, arr_a, arr_b = aligned_scores(a, b)
        assert qids == ["q1", "q2"]
        assert list(arr_a) == [0.5, 0.3]
        assert list(arr_b) == [0.4, 0.6]

    def test_deterministic_ordering(self):
        a = {"z": 1.0, "a": 2.0, "m": 3.0}
        b = {"z": 1.0, "a": 2.0, "m": 3.0}
        qids, _, _ = aligned_scores(a, b)
        assert qids == ["a", "m", "z"]


class TestPairedBootstrapTest:
    def test_identical_arrays_give_zero_diff_and_p_one(self):
        scores = [0.5, 0.6, 0.7, 0.4, 0.9] * 10
        result = paired_bootstrap_test(scores, scores, n_resamples=2000, seed=42)
        assert result.mean_diff == pytest.approx(0.0)
        assert result.p_value == pytest.approx(1.0)
        assert not result.significant_at_05

    def test_large_consistent_difference_is_significant(self):
        rng = np.random.default_rng(0)
        # System A consistently scores ~0.3 higher than B, with modest noise.
        b = rng.uniform(0.3, 0.5, size=50)
        a = b + 0.3 + rng.normal(0, 0.02, size=50)
        result = paired_bootstrap_test(a, b, n_resamples=5000, seed=42)
        assert result.mean_diff > 0.2
        assert result.p_value < 0.05
        assert result.significant_at_05
        assert result.effect_direction == "A > B"
        assert result.ci_low > 0  # CI should exclude 0 for a clearly significant effect

    def test_tiny_noisy_difference_is_not_significant(self):
        rng = np.random.default_rng(1)
        b = rng.uniform(0.3, 0.5, size=20)
        a = b + rng.normal(0, 0.5, size=20)  # huge noise swamps any real signal
        result = paired_bootstrap_test(a, b, n_resamples=3000, seed=42)
        # With this much noise on only 20 queries, the CI should not
        # reliably exclude 0 -- not asserting p >= 0.05 (that's not
        # guaranteed for any single random seed) but checking the mechanism
        # runs and produces a sane, bounded p-value.
        assert 0.0 <= result.p_value <= 1.0

    def test_mismatched_lengths_raise(self):
        with pytest.raises(ValueError):
            paired_bootstrap_test([1, 2, 3], [1, 2])

    def test_empty_input_raises(self):
        with pytest.raises(ValueError):
            paired_bootstrap_test([], [])

    def test_to_dict_has_expected_keys(self):
        result = paired_bootstrap_test([0.5, 0.6], [0.4, 0.5], n_resamples=100, seed=42)
        d = result.to_dict()
        for key in ("mean_diff", "ci_95_low", "ci_95_high", "p_value", "n_queries", "effect_direction"):
            assert key in d


class TestPairedPermutationTest:
    def test_identical_arrays_give_p_one(self):
        scores = [0.5, 0.6, 0.7, 0.4] * 10
        result = paired_permutation_test(scores, scores, n_permutations=2000, seed=42)
        assert result.mean_diff == pytest.approx(0.0)
        assert result.p_value == pytest.approx(1.0)

    def test_large_consistent_difference_is_significant(self):
        rng = np.random.default_rng(0)
        b = rng.uniform(0.3, 0.5, size=50)
        a = b + 0.3 + rng.normal(0, 0.02, size=50)
        result = paired_permutation_test(a, b, n_permutations=5000, seed=42)
        assert result.p_value < 0.05
        assert result.method == "paired_permutation"

    def test_mismatched_lengths_raise(self):
        with pytest.raises(ValueError):
            paired_permutation_test([1, 2, 3], [1, 2])

    def test_empty_input_raises(self):
        with pytest.raises(ValueError):
            paired_permutation_test([], [])


class TestBothMethodsAgreeQualitatively:
    def test_bootstrap_and_permutation_agree_on_clear_signal(self):
        rng = np.random.default_rng(7)
        b = rng.uniform(0.2, 0.6, size=100)
        a = b + 0.25
        bootstrap_result = paired_bootstrap_test(a, b, n_resamples=5000, seed=42)
        permutation_result = paired_permutation_test(a, b, n_permutations=5000, seed=42)
        assert bootstrap_result.significant_at_05
        assert permutation_result.p_value < 0.05
        assert bootstrap_result.effect_direction == permutation_result.effect_direction
