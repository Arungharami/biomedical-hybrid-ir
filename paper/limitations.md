# 13. Limitations & 14. Threats to Validity

## Known as of M0/M1 (2026-09-09)

- **Single dataset.** NFCorpus is one BEIR benchmark; findings are specific
  to its nutrition/PubMed domain and its query style (layperson health
  questions against expert biomedical text) and should not be assumed to
  generalize to other biomedical IR settings (e.g. clinical notes, TREC-COVID)
  without separate validation.
- **Local compute constraints.** Dense/cross-encoder experiments in this
  project run on a single Apple M1 Pro (MPS) or Colab GPU, not a
  large-scale cluster; efficiency numbers (Section 19) reflect that
  specific hardware and should be read as illustrative, not as
  architecture-independent throughput claims.
- **Graded relevance collapsed for some metrics.** NFCorpus qrels are
  graded (0/1/2); binary-relevance metrics (e.g. standard MRR) will use a
  documented relevance threshold — the exact threshold used is recorded in
  `docs/evaluation.md` once implemented, to avoid an unstated methodological
  choice silently affecting results.

⚪ This section will be expanded with concrete, experiment-specific
limitations as M2–M8 complete.
