#!/usr/bin/env python
"""Research CLI: immutable per-run output folders, explicit failure manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import resource
import subprocess
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from biomedical_ir.research_data import BENCHMARKS, load_benchmark
from biomedical_ir.research_pipeline import run_study


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=sorted(BENCHMARKS), required=True)
    parser.add_argument("--config", default="configs/research.json")
    parser.add_argument("--frozen-selection", help="Prior selection.json; required for test-only data")
    parser.add_argument("--output-root", default="results/research")
    parser.add_argument("--device", choices=["cpu", "cuda", "mps"])
    parser.add_argument("--rerank", action="store_true")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    if args.device:
        config["device"] = args.device
    if args.rerank:
        config["rerank"] = True
    frozen = None
    frozen_provenance = None
    if args.frozen_selection:
        content = Path(args.frozen_selection).read_bytes()
        payload = json.loads(content)
        frozen = payload["settings"]
        frozen_provenance = {"path": args.frozen_selection,
                             "sha256": hashlib.sha256(content).hexdigest(),
                             "source_dataset": payload["source_dataset"]}
        if frozen_provenance["source_dataset"]["dataset"] == f"BeIR/{args.dataset}":
            parser.error("Frozen transfer settings must originate from a different benchmark")
    started = datetime.now(timezone.utc)
    output = Path(args.output_root) / args.dataset / started.strftime("%Y%m%dT%H%M%S%fZ")
    output.mkdir(parents=True, exist_ok=False)
    git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    manifest = {"status": "running", "started": started.isoformat(), "config": config,
                "dataset": args.dataset, "frozen_selection": frozen_provenance,
                "python": platform.python_version(), "git_commit": git.stdout.strip() or None,
                "evaluation_population": "all official test queries with judgments",
                "primary_metric": "nDCG@10", "subgroups": "predefined descriptive strata"}
    try:
        import numpy as np
        import torch
        np.random.seed(config["seed"])
        torch.manual_seed(config["seed"])
        manifest["hardware"] = {"platform": platform.platform(), "device": config["device"],
            "cuda_available": torch.cuda.is_available(),
            "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}
        manifest["packages"] = {p: version(p) for p in ("numpy", "datasets", "transformers",
            "sentence-transformers", "torch", "scikit-learn", "huggingface-hub", "pytrec-eval")}
        data = load_benchmark(args.dataset, seed=config["seed"])
        manifest["data_provenance"] = data.provenance
        report = run_study(data, config, output, frozen=frozen)
        manifest["model_shas"] = report["model_shas"]
        manifest["status"] = "complete"
        print(f"Research outputs: {output}")
    except Exception as exc:
        manifest.update(status="failed", error=repr(exc))
        raise
    finally:
        manifest["finished"] = datetime.now(timezone.utc).isoformat()
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        manifest["peak_process_rss_bytes"] = rss if platform.system() == "Darwin" else rss * 1024
        manifest["memory_note"] = "Cumulative process peak RSS; excludes GPU memory"
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
