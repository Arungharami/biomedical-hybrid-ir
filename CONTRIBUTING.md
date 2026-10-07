# Contributing

Useful contributions to **biomedical-hybrid-ir** include:

- Reproduce one baseline and report your environment, commands, and any setup failure.
- Investigate a query where lexical and dense retrieval disagree using the committed rankings.
- Improve installation instructions with a clean-environment reproduction report.

## Reporting a problem

Check existing issues first. Include the source commit or branch, environment, minimal steps, expected behavior, actual behavior, and a redacted error. State whether you used real data, an educational fixture, or exported results. Keep credentials and personal records out of public reports.

## Proposing a change

Choose one bounded task. Describe the intended behavior and how it will be checked before a large implementation. Use a focused branch and draft pull request; link any existing issue. Record exactly which checks ran, including failures and unavailable checks. Do not report a full suite as passed after running only a subset.

## Relevant local checks

These are focused checks, not a replacement for the full project workflow in the README.

```bash
PYTHONPATH=src python examples/tfidf_quickstart.py
PYTHONPATH=src python -m unittest discover -s tests -p test_missing_query_regressions.py -v
```

## Project evidence and boundaries

The three hand-written documents in the offline example are educational fixtures, not NFCorpus data or benchmark evidence. Full research evaluation uses the documented dataset, qrels, and evaluator.

[Project overview and setup](README.md) · [Issues](https://github.com/Arungharami/biomedical-hybrid-ir/issues) · [Author's portfolio](https://arungharami.info)
