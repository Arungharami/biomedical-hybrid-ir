# Main results (NFCorpus, test split, n=323 queries)

> Generated from `results/metrics/{tfidf,bm25}.json` (M2). Rows for M3-M6
> are `Pending` until their milestones produce real artifacts under
> `results/metrics/` -- no number below is fabricated or estimated in
> advance of its actual run. Metrics computed with `pytrec_eval` against
> `data/raw/nfcorpus/qrels_test.json`; see `src/biomedical_ir/evaluation.py`
> for the exact measure definitions and graded-relevance handling.
> Latency = mean top-100 retrieval wall-clock time per query (CPU), from
> each run's `timing.latency_ms_per_query`.

| Model | P@10 | Recall@100 | MAP | MRR@10 | nDCG@10 | Latency (ms/query) |
|---|---:|---:|---:|---:|---:|---:|
| TF-IDF | 0.2167 | 0.2372 | 0.1372 | 0.5062 | 0.3050 | 3.631 |
| BM25 (k1=1.2, b=0.75) | 0.2071 | 0.2295 | 0.1333 | 0.4939 | 0.2954 | 2.155 |
| BGE (general dense) | Pending | Pending | Pending | Pending | Pending | Pending |
| MedCPT (biomedical dense) | Pending | Pending | Pending | Pending | Pending | Pending |
| BM25 + MedCPT (RRF) | Pending | Pending | Pending | Pending | Pending | Pending |
| Hybrid + MedCPT Cross-Encoder Reranker | Pending | Pending | Pending | Pending | Pending | Pending |

## M2 observation (raw numbers only, no significance claim)

On this run, TF-IDF's point estimates are numerically higher than BM25's on
every reported metric (e.g. nDCG@10: TF-IDF 0.3050 vs. BM25 0.2954; MAP:
0.1372 vs. 0.1333) -- the opposite direction from H1 ("BM25 will outperform
standard TF-IDF"). This is reported as-is; no parameter was tuned against
the test set to change it (`configs/bm25.yaml` uses the frozen literature
defaults k1=1.2, b=0.75, `tuning.enabled: false`). Whether this difference
is statistically meaningful is **not** evaluated here -- paired
significance testing across all model pairs is M7's job
(`src/biomedical_ir/statistics.py`, not yet implemented). H1 remains an
open hypothesis, not confirmed or rejected, until that test runs.
