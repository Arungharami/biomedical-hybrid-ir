# Evaluation

> Status: implementation landed in M2 (`src/biomedical_ir/evaluation.py`),
> exercised on all six models (M2-M6). Statistical testing (M7) complete --
> see `results/tables/statistical_tests.md` and the Statistical testing
> section below.

## Metrics

Precision@{1,5,10}, Recall@{10,20,50,100}, MRR, MRR@10, MAP, MAP@100,
nDCG@{5,10,20}. Computed with `pytrec_eval` (a Python wrapper around the
official `trec_eval` C implementation) as the source of truth, and
cross-checked against custom implementations in
`src/biomedical_ir/evaluation.py` for educational transparency and as a
correctness check (`tests/test_metrics.py`). Because `top_k=100` is used for
both TF-IDF and BM25 retrieval, `MAP` and `MAP@100` are numerically
identical in the M2 results -- documented rather than treated as a bug.

## Graded relevance handling (investigated empirically, not assumed)

NFCorpus qrels are graded (0/1/2). Directly probing `pytrec_eval` with a
hand-built graded example (reproduced in
`tests/test_metrics.py::TestGradedRelevanceHandling`) established:

- Binary-style measures (P.k, recall.k, map, map_cut.k, recip_rank/MRR)
  treat any relevance grade `> 0` as relevant -- no manual threshold is
  applied anywhere in this project's code; `pytrec_eval`/`trec_eval`
  already does the right thing by default.
- `P.k` divides by `k` itself, not by the number of documents actually
  retrieved (a query with fewer than `k` retrieved documents is penalized).
- `ndcg_cut.k` uses the graded relevance value as a **linear** gain
  (`gain(rel) = rel`), not the exponential-gain variant
  (`gain(rel) = 2**rel - 1`) some other libraries default to -- verified
  by comparing both formulas' output against `pytrec_eval`'s on a
  synthetic graded example.
- A query with zero relevant documents in qrels evaluates to `0.0` for
  every measure (not `NaN`, not skipped).

Our custom from-scratch implementations replicate all of the above exactly
and are unit-tested to agree with `pytrec_eval` within floating-point
tolerance.

## Protocol

- Every model is evaluated against the **same** `test` split qrels
  (`data/raw/nfcorpus/qrels_test.json` / regenerated via
  `scripts/audit_dataset.py`).
- Any parameter tuning (BM25 k1/b, RRF k) happens on `dev` only and is
  frozen in the relevant config before test-set evaluation runs — see
  Section 4 of the project spec and `docs/dataset.md`.

## Statistical testing ✅ M7 complete

Paired bootstrap testing (`src/biomedical_ir/statistics.py`,
n_resamples=10000, seed=42) at the query level, run by
`scripts/evaluate_all.py`. Six comparisons x five primary metrics = 30
tests: the five Section 16 names explicitly (BM25 vs BGE, BM25 vs MedCPT,
BGE vs MedCPT, MedCPT vs Hybrid, Hybrid vs Hybrid+Reranker) plus TF-IDF vs
BM25 (added to directly resolve H1). Every model's per-query scores are
loaded from `results/runs/*.json` (not `*.trec`) specifically so BM25's 25
zero-result test queries participate in the pairing rather than vanishing
(see `evaluation.load_run_json`'s docstring). Full results:
`results/tables/statistical_tests.md` / `.json`.

**Headline results:** both dense retrievers (BGE, MedCPT) significantly
beat BM25 on all five primary metrics (p<0.005 each) — the study's most
robust finding. H1 is rejected (TF-IDF significantly beats BM25); H2 and
H3 (for the comparisons actually tested) are not supported; H4 is
partially supported (latency increase unambiguous, but its flagship
nDCG@10 claim, while the best point estimate in the study, is not
significant at p=0.194). See `paper/methodology.md` for the full
per-hypothesis verdicts and `paper/results.md` Section 9 for the complete
writeup.

A permutation test (`paired_permutation_test`, same module) is also
implemented and unit-tested as a second method, per Section 16's "prefer
paired bootstrap or permutation/randomization testing" — the bootstrap test
is used as the project's primary reported method since it directly yields
both a confidence interval and a p-value together.
