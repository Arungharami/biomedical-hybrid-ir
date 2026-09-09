# 13. Limitations & 14. Threats to Validity

## Scope and generalization

- **Single dataset.** NFCorpus is one BEIR benchmark, drawn from
  NutritionFacts.org queries against PubMed-indexed articles. Findings are
  specific to that domain and query style (layperson health questions
  against expert biomedical text) and should not be assumed to generalize
  to other biomedical IR settings (clinical notes, TREC-COVID, drug
  interaction lookup, etc.) without separate validation.
- **Single test split, n=323 queries.** All significance tests in this
  study operate on a fixed set of 323 test queries. Several comparisons
  that show a large raw difference but fail significance (e.g. reranking's
  nDCG@10 gain, p=0.194) might resolve differently with a larger query
  set — "not significant at n=323" is not the same claim as "no true
  effect exists."

## Methodology-specific limitations, discovered during this study

- **Graded relevance handled via a fixed threshold for binary measures.**
  NFCorpus qrels are graded (0/1/2); `pytrec_eval`'s binary-style measures
  (P@k, Recall@k, MRR, MAP) treat any grade >0 as relevant, verified
  empirically rather than assumed (`docs/evaluation.md`). A different
  threshold choice (e.g. requiring grade=2) could change results and was
  not explored as a separate ablation.
- **The cross-encoder reranker's Recall@100/MAP are not directly
  comparable to the other five models' true top-100 rankings** — a
  reranker restricted to reordering its candidate pool cannot recover
  recall beyond that pool's size, so Recall@k for k exceeding the pool is
  identical to Recall@pool by mathematical construction (verified exactly
  in `results/tables/main_results.md`'s M6 section and the A6 ablation).
  This is documented and worked around by reporting pool=100's numbers
  alongside the default (pool=50), but readers comparing the main table's
  single reranked row against the other rows should keep this caveat in
  mind.
- **Only five (six, including the added H1 test) of the many possible
  pairwise comparisons were run statistically.** Direct BM25-vs-Hybrid-RRF
  and BGE-vs-Hybrid-RRF tests, for instance, were not performed — they
  fall outside the five comparisons the project's evaluation protocol
  names explicitly (Section 16). Where this matters (H3's BM25 half), it
  is flagged specifically rather than silently treated as tested.

## Compute and hardware

- **Local compute constraints.** All dense/cross-encoder experiments ran
  on a single Apple M1 Pro (MPS backend), not a GPU cluster. Cross-encoder
  reranking latency in particular (~765-3918 ms/query depending on
  candidate pool) is almost certainly not representative of GPU-optimized
  production latency — PyTorch's MPS backend lacks some of CUDA's fused
  attention kernels for transformer inference. Reported as a real,
  honest measurement on the hardware actually used (Section 22 of the
  project spec), not extrapolated to a hypothetical GPU number.
- **Embeddings are not cached to disk between runs.** Each script
  invocation (BGE, MedCPT, reranker) re-encodes from scratch. This is fine
  at NFCorpus's scale (3,633 documents) but would need addressing for a
  larger corpus, per `scripts/reproduce.py`'s "resume from cache"
  requirement (Section 24) not being fully honored at the embedding level.

## What this study does NOT claim

- It does not claim BM25 is generally inferior to TF-IDF — only that it
  was, significantly, on this specific dataset with these specific frozen
  parameters.
- It does not claim biomedical-domain pretraining is not useful in
  general — only that MedCPT did not significantly outperform a strong
  general-purpose baseline (BGE) on this specific test set.
- It does not claim cross-encoder reranking is not worth doing — its
  P@10 gain is real and significant, and its nDCG@10 point estimate is the
  best in the study; it claims specifically that the nDCG@10 gain does not
  clear conventional statistical significance at n=323, which is a
  narrower and more precise claim.
