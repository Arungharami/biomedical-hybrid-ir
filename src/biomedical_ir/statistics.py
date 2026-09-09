"""Paired, query-level statistical significance testing (M7, Section 16 of the
project spec).

Two methods are provided, both operating on PAIRED per-query metric scores
(the same queries, same metric, two different models/systems) -- never on
the mean difference alone, per Section 16's explicit instruction:

- :func:`paired_bootstrap_test` -- resamples queries with replacement,
  reporting the mean difference, a confidence interval, and a p-value.
- :func:`paired_permutation_test` -- randomly flips the sign of each
  paired per-query difference (equivalent to randomly swapping which
  system "wins" that query), reporting a p-value against the null
  hypothesis of no systematic difference.

Both require the SAME set of queries to be scored by both systems (the
"paired" in paired testing) -- callers are responsible for aligning
per-query score arrays to a common, ordered query ID list before calling
either function (e.g. via :func:`aligned_scores`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass
class SignificanceResult:
    metric: str
    model_a: str
    model_b: str
    mean_a: float
    mean_b: float
    mean_diff: float  # mean_a - mean_b; positive means a scored higher on average
    ci_low: float
    ci_high: float
    p_value: float
    n_queries: int
    n_resamples: int
    method: str

    @property
    def effect_direction(self) -> str:
        if self.mean_diff > 0:
            return f"{self.model_a} > {self.model_b}"
        if self.mean_diff < 0:
            return f"{self.model_b} > {self.model_a}"
        return "no difference"

    @property
    def significant_at_05(self) -> bool:
        return self.p_value < 0.05

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "model_a": self.model_a,
            "model_b": self.model_b,
            "mean_a": round(self.mean_a, 6),
            "mean_b": round(self.mean_b, 6),
            "mean_diff": round(self.mean_diff, 6),
            "ci_95_low": round(self.ci_low, 6),
            "ci_95_high": round(self.ci_high, 6),
            "p_value": round(self.p_value, 6),
            "n_queries": self.n_queries,
            "n_resamples": self.n_resamples,
            "method": self.method,
            "effect_direction": self.effect_direction,
            "significant_at_alpha_0.05": self.significant_at_05,
        }


def aligned_scores(
    per_query_a: dict[str, float], per_query_b: dict[str, float]
) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Restrict two per-query score dicts to their common query IDs (sorted for
    determinism) and return parallel numpy arrays -- the "pairing" step."""
    common_qids = sorted(set(per_query_a.keys()) & set(per_query_b.keys()))
    a = np.array([per_query_a[q] for q in common_qids], dtype=float)
    b = np.array([per_query_b[q] for q in common_qids], dtype=float)
    return common_qids, a, b


def paired_bootstrap_test(
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    *,
    metric: str = "",
    model_a: str = "A",
    model_b: str = "B",
    n_resamples: int = 10000,
    seed: int = 42,
    ci_level: float = 0.95,
) -> SignificanceResult:
    """Paired bootstrap significance test over per-query score differences.

    Resamples query INDICES with replacement (so a query's (a, b) pair is
    always resampled together -- that is what makes this "paired"), computes
    the mean difference for each resample, and reports:

    - ``mean_diff`` = observed mean(a) - mean(b) (not the bootstrap mean)
    - a ``ci_level`` confidence interval from the resample distribution's
      percentiles
    - a two-sided p-value: 2 * min(P(bootstrap diff <= 0), P(bootstrap diff >= 0)),
      capped at 1.0 -- the standard bootstrap-hypothesis-test construction
      (Efron & Tibshirani, 1993) for "is 0 outside the plausible range of
      differences".
    """
    a = np.asarray(scores_a, dtype=float)
    b = np.asarray(scores_b, dtype=float)
    if len(a) != len(b):
        raise ValueError("scores_a and scores_b must be the same length (paired)")
    n = len(a)
    if n == 0:
        raise ValueError("cannot run a significance test on zero queries")

    rng = np.random.default_rng(seed)
    diffs = a - b
    observed_mean_diff = float(diffs.mean())

    resample_indices = rng.integers(0, n, size=(n_resamples, n))
    resampled_diffs = diffs[resample_indices]  # shape (n_resamples, n)
    resample_means = resampled_diffs.mean(axis=1)

    alpha = 1 - ci_level
    ci_low, ci_high = np.percentile(resample_means, [100 * alpha / 2, 100 * (1 - alpha / 2)])

    p_ge_zero = float(np.mean(resample_means >= 0))
    p_le_zero = float(np.mean(resample_means <= 0))
    p_value = min(1.0, 2 * min(p_ge_zero, p_le_zero))

    return SignificanceResult(
        metric=metric,
        model_a=model_a,
        model_b=model_b,
        mean_a=float(a.mean()),
        mean_b=float(b.mean()),
        mean_diff=observed_mean_diff,
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        p_value=p_value,
        n_queries=n,
        n_resamples=n_resamples,
        method="paired_bootstrap",
    )


def paired_permutation_test(
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    *,
    metric: str = "",
    model_a: str = "A",
    model_b: str = "B",
    n_permutations: int = 10000,
    seed: int = 42,
) -> SignificanceResult:
    """Paired randomization/permutation test.

    Under the null hypothesis (no systematic difference between the two
    systems), swapping which system "wins" a given query is exchangeable --
    so each per-query difference's SIGN is randomly flipped ``n_permutations``
    times, and the p-value is the fraction of permuted mean-|diff|s at least
    as extreme as the observed one (two-sided).

    No confidence interval is produced by a permutation test (it tests a
    hypothesis, it does not estimate an interval) -- ``ci_low``/``ci_high``
    are set to the observed mean_diff itself as a degenerate placeholder, so
    callers should read ``p_value`` as this method's primary output.
    """
    a = np.asarray(scores_a, dtype=float)
    b = np.asarray(scores_b, dtype=float)
    if len(a) != len(b):
        raise ValueError("scores_a and scores_b must be the same length (paired)")
    n = len(a)
    if n == 0:
        raise ValueError("cannot run a significance test on zero queries")

    rng = np.random.default_rng(seed)
    diffs = a - b
    observed_mean_diff = float(diffs.mean())
    observed_abs = abs(observed_mean_diff)

    signs = rng.choice([-1.0, 1.0], size=(n_permutations, n))
    permuted_means = (signs * diffs).mean(axis=1)

    p_value = float(np.mean(np.abs(permuted_means) >= observed_abs))

    return SignificanceResult(
        metric=metric,
        model_a=model_a,
        model_b=model_b,
        mean_a=float(a.mean()),
        mean_b=float(b.mean()),
        mean_diff=observed_mean_diff,
        ci_low=observed_mean_diff,
        ci_high=observed_mean_diff,
        p_value=p_value,
        n_queries=n,
        n_resamples=n_permutations,
        method="paired_permutation",
    )
