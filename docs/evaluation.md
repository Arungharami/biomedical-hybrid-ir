# Evaluation

> Status: stub — implementation lands in M2 (first real metrics) and M7
> (full table + statistical testing). Metric definitions below are final;
> numbers will be filled in as real runs complete.

## Metrics

Precision@{1,5,10}, Recall@{10,20,50,100}, MRR, MRR@10, MAP, MAP@100,
nDCG@{5,10,20}. Computed with `pytrec_eval` (a Python wrapper around the
official `trec_eval` C implementation) as the source of truth, and
cross-checked against custom implementations in
`src/biomedical_ir/evaluation.py` for educational transparency and as a
correctness check (`tests/test_metrics.py`).

## Protocol

- Every model is evaluated against the **same** `test` split qrels
  (`data/raw/nfcorpus/qrels_test.json` / regenerated via
  `scripts/audit_dataset.py`).
- Any parameter tuning (BM25 k1/b, RRF k) happens on `dev` only and is
  frozen in the relevant config before test-set evaluation runs — see
  Section 4 of the project spec and `docs/dataset.md`.

## Statistical testing

Paired bootstrap / permutation testing at the query level for the key model
comparisons (BM25 vs BGE, BM25 vs MedCPT, BGE vs MedCPT, MedCPT vs Hybrid,
Hybrid vs Hybrid+Reranker). Reports metric difference, confidence interval,
p-value, effect direction, and number of queries — implemented in
`src/biomedical_ir/statistics.py`. ⚪ Pending (M7).
