#!/usr/bin/env python
"""Aggregate completed benchmark runs and correct the full study family."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from biomedical_ir.research_stats import holm_adjust


def aggregate(paths):
    benchmarks, all_comparisons, reference = {}, [], None
    for path in paths:
        path = Path(path)
        manifest = json.loads((path / "manifest.json").read_text())
        report = json.loads((path / "report.json").read_text())
        if manifest["status"] != "complete":
            raise ValueError(f"Not a completed experiment: {path}")
        name = manifest["dataset"]
        if name in benchmarks:
            raise ValueError(f"Choose exactly one run per benchmark: {name}")
        cfg = manifest["config"]
        signature = (cfg["candidate_depth"], cfg["dense_methods"], cfg["rerank"],
                     report["model_shas"], sorted(report["metrics"]))
        if reference is not None and signature != reference:
            raise ValueError("Benchmark runs use incompatible systems, model SHAs or budgets")
        reference = signature
        benchmarks[name] = {"path": str(path), "summary": {
            system: result["summary"] for system, result in report["metrics"].items()},
            "primary_mean_ci95": report["primary_mean_ci95"]}
        all_comparisons.extend({"dataset": name, **row} for row in report["statistics"]["comparisons"])
    if not benchmarks:
        raise ValueError("No benchmark runs")
    adjusted = holm_adjust([row["p_value"] for row in all_comparisons])
    for row, p in zip(all_comparisons, adjusted):
        row.update(p_holm_study=p, reject_study_at_05=p < 0.05)
    return {"benchmarks": benchmarks, "study_family_size": len(all_comparisons),
            "study_family": "all primary nDCG@10 contrasts across supplied benchmarks",
            "comparisons": all_comparisons,
            "note": "Dataset-level intervals remain pointwise; global Holm controls this study family"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", nargs="+")
    parser.add_argument("--output", default="results/research/study-summary.json")
    args = parser.parse_args()
    report = aggregate(args.runs)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(output)


if __name__ == "__main__":
    main()
