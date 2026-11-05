"""Paired effect intervals, Monte Carlo randomization and Holm adjustment."""

from __future__ import annotations

import math

import numpy as np


def holm_adjust(p_values):
    if any(not math.isfinite(p) or not 0 <= p <= 1 for p in p_values):
        raise ValueError("P-values must be finite and between 0 and 1")
    order = sorted(range(len(p_values)), key=lambda i: (p_values[i], i))
    result, previous = [0.0] * len(order), 0.0
    for rank, index in enumerate(order):
        previous = max(previous, min(1.0, (len(order) - rank) * p_values[index]))
        result[index] = previous
    return result


def paired_effect(a, b, resamples=10000, seed=42):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.ndim != 1 or a.shape != b.shape or not len(a):
        raise ValueError("Need nonempty aligned one-dimensional scores")
    if not np.isfinite(a).all() or not np.isfinite(b).all() or resamples < 100:
        raise ValueError("Finite scores and at least 100 resamples required")
    rng = np.random.default_rng(seed)
    differences = a - b
    observed = float(differences.mean())
    bootstrap, extreme = [], 0
    # Chunk resampling to avoid memory proportional to all permutations × all queries.
    for start in range(0, resamples, 128):
        count = min(128, resamples - start)
        idx = rng.integers(0, len(a), size=(count, len(a)))
        bootstrap.extend(differences[idx].mean(axis=1).tolist())
        signs = rng.choice([-1, 1], size=(count, len(a)))
        permuted = (signs * differences).mean(axis=1)
        extreme += int((np.abs(permuted) >= abs(observed) - 1e-15).sum())
    low, high = np.quantile(bootstrap, [0.025, 0.975])
    return {"mean_difference": observed, "ci95_low": float(low), "ci95_high": float(high),
            "p_value": (extreme + 1) / (resamples + 1), "queries": len(a),
            "resamples": resamples, "seed": seed,
            "ci_method": "paired percentile bootstrap",
            "p_method": "two-sided paired Monte Carlo sign randomization; plus-one correction"}


def comparison_report(per_system, comparisons, resamples=10000, seed=42):
    """One predeclared primary nDCG@10 family per dataset; no intersection dropping."""
    rows = []
    for a, b in comparisons:
        left, right = per_system[a], per_system[b]
        if set(left) != set(right):
            raise ValueError("Statistical comparisons require identical query IDs")
        ids = sorted(left)
        effect = paired_effect([left[q] for q in ids], [right[q] for q in ids], resamples, seed)
        rows.append({"system_a": a, "system_b": b, "metric": "nDCG@10", **effect})
    for row, adjusted in zip(rows, holm_adjust([r["p_value"] for r in rows])):
        row.update(p_holm=adjusted, reject_at_05=adjusted < 0.05)
    return {"family": "all planned primary nDCG@10 contrasts within this dataset",
            "family_size": len(rows), "correction": "Holm", "comparisons": rows,
            "intervals": "Pointwise 95% effect intervals; not simultaneous family intervals"}
