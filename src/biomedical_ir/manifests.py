"""Experiment manifest creation and validation (see results/manifests/).

Every retrieval/evaluation run writes one manifest documenting exactly what
was run, on what data/model revisions, with what parameters, so results can
be traced back to a reproducible configuration (Section 20 / 41 of the
project spec).
"""

from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .utils import REPO_ROOT, get_git_commit, library_versions

REQUIRED_FIELDS = [
    "experiment_id",
    "timestamp",
    "git_commit",
    "dataset",
    "split",
    "model",
    "parameters",
    "seed",
    "device",
    "python_version",
    "library_versions",
    "runtime_seconds",
    "status",
]

VALID_STATUSES = {"pending", "running", "complete", "failed"}


def build_manifest(
    experiment_id: str,
    dataset: str,
    split: str,
    model: str,
    parameters: dict[str, Any],
    seed: int,
    device: str,
    runtime_seconds: float,
    status: str,
    *,
    dataset_revision: str | None = None,
    model_revision: str | None = None,
    error: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {VALID_STATUSES}, got {status!r}")

    manifest = {
        "experiment_id": experiment_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_git_commit(),
        "dataset": dataset,
        "dataset_revision": dataset_revision,
        "split": split,
        "model": model,
        "model_revision": model_revision,
        "parameters": parameters,
        "seed": seed,
        "device": device,
        "python_version": platform.python_version(),
        "os": f"{platform.system()} {platform.release()}",
        "library_versions": library_versions(),
        "runtime_seconds": round(runtime_seconds, 4),
        "status": status,
    }
    if error is not None:
        manifest["error"] = error
    if extra:
        manifest.update(extra)
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    """Return a list of validation problems (empty list = valid)."""
    problems = []
    for field in REQUIRED_FIELDS:
        if field not in manifest:
            problems.append(f"missing required field: {field}")
    if manifest.get("status") not in VALID_STATUSES:
        problems.append(f"invalid status: {manifest.get('status')!r}")
    if manifest.get("status") == "failed" and "error" not in manifest:
        problems.append("status is 'failed' but no 'error' field is present")
    runtime = manifest.get("runtime_seconds")
    if runtime is not None and (not isinstance(runtime, (int, float)) or runtime < 0):
        problems.append("runtime_seconds must be a non-negative number")
    return problems


def save_manifest(manifest: dict[str, Any], manifests_dir: str | Path = None) -> Path:
    problems = validate_manifest(manifest)
    if problems:
        raise ValueError(f"Invalid manifest for {manifest.get('experiment_id')}: {problems}")

    manifests_dir = Path(manifests_dir) if manifests_dir else REPO_ROOT / "results" / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    out_path = manifests_dir / f"{manifest['experiment_id']}.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=False)
    return out_path
