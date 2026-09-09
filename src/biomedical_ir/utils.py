"""Shared utilities: config loading, seeding, device detection, timing."""

from __future__ import annotations

import os
import random
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIGS_DIR = REPO_ROOT / "configs"


def load_config(name_or_path: str) -> dict[str, Any]:
    """Load a YAML config, resolving a single-level ``extends: <file>`` chain.

    ``name_or_path`` may be a bare filename (resolved under configs/) or a
    full path. Keys in the child config override keys in the parent config;
    nested dicts are merged one level deep (sufficient for this project's
    configs).
    """
    path = Path(name_or_path)
    if not path.is_absolute() and not path.exists():
        path = CONFIGS_DIR / name_or_path
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {name_or_path}")

    with open(path) as f:
        cfg = yaml.safe_load(f) or {}

    parent_name = cfg.pop("extends", None)
    if parent_name:
        parent_path = Path(parent_name)
        if not parent_path.is_absolute():
            parent_path = path.parent / parent_name
        parent_cfg = load_config(str(parent_path))
        cfg = _merge_dicts(parent_cfg, cfg)

    return cfg


def _merge_dicts(base: dict, override: dict) -> dict:
    merged = dict(base)
    for k, v in override.items():
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = _merge_dicts(merged[k], v)
        else:
            merged[k] = v
    return merged


def set_seed(seed: int = 42) -> None:
    """Seed python, numpy, and torch (if importable) for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def detect_device(preference: str = "auto") -> str:
    """Return 'cuda', 'mps', or 'cpu'.

    ``preference`` of 'auto' picks the best available accelerator, preferring
    CUDA (Colab/most cloud GPUs) then Apple MPS (local Apple Silicon) then CPU.
    An explicit preference is honored if that backend is actually available,
    otherwise falls back to auto behavior with a warning.
    """
    try:
        import torch
    except ImportError:
        return "cpu"

    available = {
        "cuda": torch.cuda.is_available(),
        "mps": getattr(torch.backends, "mps", None) is not None
        and torch.backends.mps.is_available(),
        "cpu": True,
    }

    if preference != "auto":
        if available.get(preference, False):
            return preference
        print(
            f"[device] requested '{preference}' not available, falling back to auto-detect",
            file=sys.stderr,
        )

    if available["cuda"]:
        return "cuda"
    if available["mps"]:
        return "mps"
    return "cpu"


def get_git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except Exception:
        return "unknown"


def library_versions() -> dict[str, str]:
    versions: dict[str, str] = {"python": sys.version.split()[0]}
    for pkg in [
        "numpy",
        "scipy",
        "pandas",
        "sklearn",
        "torch",
        "transformers",
        "sentence_transformers",
        "datasets",
        "faiss",
        "pytrec_eval",
    ]:
        try:
            mod = __import__(pkg)
            versions[pkg] = getattr(mod, "__version__", "unknown")
        except ImportError:
            versions[pkg] = "not installed"
    return versions


@contextmanager
def timer():
    """Context manager yielding a dict populated with elapsed seconds on exit."""
    state: dict[str, float] = {}
    start = time.perf_counter()
    try:
        yield state
    finally:
        state["elapsed_seconds"] = time.perf_counter() - start


def ensure_dirs(*dirs: str | Path) -> None:
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
