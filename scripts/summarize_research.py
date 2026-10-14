#!/usr/bin/env python
"""Aggregate completed benchmark runs and correct the full study family."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from biomedical_ir.research_reporting import aggregate



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
