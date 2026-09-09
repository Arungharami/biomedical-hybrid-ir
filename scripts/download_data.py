#!/usr/bin/env python
"""Download NFCorpus (corpus, queries, qrels) from Hugging Face and cache it locally.

Thin wrapper around biomedical_ir.data.load_nfcorpus; see
scripts/audit_dataset.py for download + validation + stats generation in one step.

Usage:
    python scripts/download_data.py [--config configs/default.yaml]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from biomedical_ir.data import load_nfcorpus  # noqa: E402
from biomedical_ir.utils import load_config  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    ds_cfg = cfg["dataset"]

    data = load_nfcorpus(
        cache_dir=ds_cfg["cache_dir"],
        raw_dir=ds_cfg["raw_dir"],
        splits=tuple(ds_cfg["splits"]),
    )

    print(f"corpus documents: {len(data.corpus)}")
    print(f"queries:          {len(data.queries)}")
    for split, split_qrels in data.qrels.items():
        if split.startswith("_"):
            continue
        print(f"qrels[{split}]: {len(split_qrels)} queries")
    print(f"Saved raw dump under {ds_cfg['raw_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
