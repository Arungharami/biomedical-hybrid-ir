#!/usr/bin/env python
"""One-command reproduction of the full pipeline (Section 24 of the project spec).

Runs, in order: dataset audit -> TF-IDF -> BM25 -> BGE -> MedCPT -> hybrid
RRF -> cross-encoder reranking -> full evaluation (statistical + efficiency)
-> error analysis. Each step is SKIPPED if its expected output artifact
already exists, so expensive embedding steps (BGE, MedCPT, reranking) are
never silently recomputed -- pass --force to recompute everything anyway.

Web export (Section 24's final step) is deferred to
scripts/export_web_results.py once that script exists (M11); this
orchestrator calls it automatically if present.

Usage:
    python scripts/reproduce.py [--config configs/default.yaml] [--force] [--from STEP]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# (step name, script path, list of expected output files that mean "already done")
STEPS: list[tuple[str, str, list[str]]] = [
    ("dataset_audit", "scripts/audit_dataset.py", ["data/processed/dataset_stats.json"]),
    ("tfidf", "scripts/run_tfidf.py", ["results/metrics/tfidf.json"]),
    ("bm25", "scripts/run_bm25.py", ["results/metrics/bm25.json"]),
    ("bge", "scripts/run_bge.py", ["results/metrics/bge.json"]),
    ("medcpt", "scripts/run_medcpt.py", ["results/metrics/medcpt.json"]),
    ("hybrid", "scripts/run_hybrid.py", ["results/metrics/hybrid_rrf.json"]),
    ("reranker", "scripts/run_reranker.py", ["results/metrics/hybrid_reranked.json"]),
    ("evaluate_all", "scripts/evaluate_all.py", ["results/tables/statistical_tests.json"]),
    ("error_analysis", "scripts/error_analysis.py", ["results/error-analysis/error_analysis.json"]),
]

# Optional final step -- run only if the script exists (M11 deliverable).
OPTIONAL_STEPS: list[tuple[str, str, list[str]]] = [
    ("web_export", "scripts/export_web_results.py", ["web/data/metrics.json"]),
]


def outputs_exist(paths: list[str]) -> bool:
    return all((REPO_ROOT / p).exists() for p in paths)


def run_step(name: str, script: str, config: str | None, force: bool, outputs: list[str]) -> bool:
    """Returns True on success (including skipped), False on failure."""
    if not force and outputs_exist(outputs):
        print(f"[reproduce] SKIP  {name} (already exists: {outputs[0]})")
        return True

    cmd = [sys.executable, script]
    if config:
        cmd += ["--config", config]

    print(f"[reproduce] RUN   {name}: {' '.join(cmd)}")
    start = time.perf_counter()
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    elapsed = time.perf_counter() - start

    if result.returncode != 0:
        print(f"[reproduce] FAIL  {name} (exit code {result.returncode}, {elapsed:.1f}s)", file=sys.stderr)
        return False

    print(f"[reproduce] DONE  {name} ({elapsed:.1f}s)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--force", action="store_true", help="recompute every step, ignoring cached artifacts")
    parser.add_argument(
        "--from",
        dest="from_step",
        default=None,
        help="resume starting from this step name (skips everything before it unconditionally)",
    )
    args = parser.parse_args()

    all_steps = STEPS
    if args.from_step:
        names = [s[0] for s in all_steps]
        if args.from_step not in names:
            print(f"[reproduce] ERROR: unknown step {args.from_step!r}. Valid: {names}", file=sys.stderr)
            return 1
        all_steps = all_steps[names.index(args.from_step) :]

    pipeline_start = time.perf_counter()
    for name, script, outputs in all_steps:
        # Note: per-model configs live under configs/<model>.yaml, not the
        # single --config passed in; each run_*.py script defaults to its
        # own config already, so we only forward --config to steps that
        # accept configs/default.yaml-shaped configs directly.
        step_config = args.config if name in ("dataset_audit", "evaluate_all", "error_analysis") else None
        ok = run_step(name, script, step_config, args.force, outputs)
        if not ok:
            print(f"[reproduce] Pipeline stopped at step '{name}'. Fix the error above and re-run "
                  f"with --from {name} to resume.", file=sys.stderr)
            return 1

    for name, script, outputs in OPTIONAL_STEPS:
        if not (REPO_ROOT / script).exists():
            print(f"[reproduce] SKIP  {name} ({script} does not exist yet)")
            continue
        ok = run_step(name, script, None, args.force, outputs)
        if not ok:
            return 1

    total = time.perf_counter() - pipeline_start
    print(f"\n[reproduce] Pipeline complete in {total:.1f}s.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
