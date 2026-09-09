# 3. Research Questions & 5. Methodology

## 3. Research Questions

**RQ1.** How does BM25 compare with TF-IDF for biomedical retrieval on NFCorpus?

**RQ2.** Does dense semantic retrieval improve retrieval effectiveness compared with traditional lexical methods?

**RQ3.** Does a biomedical-domain retrieval model such as MedCPT outperform a general-purpose dense retrieval model?

**RQ4.** Does hybrid lexical-semantic retrieval outperform BM25 and MedCPT individually?

**RQ5.** Does biomedical cross-encoder reranking improve top-ranked retrieval effectiveness?

**RQ6.** What effectiveness/efficiency trade-offs exist among traditional, dense, hybrid, and reranked retrieval systems?

## Hypotheses

These were stated as hypotheses to be tested before any experiment ran.
M7's paired bootstrap significance tests (`results/tables/statistical_tests.md`,
`src/biomedical_ir/statistics.py`) have now run against all real results
(M2-M6); each hypothesis's verdict below is stated precisely and is not
overstated beyond what the test actually shows.

**H1.** BM25 will outperform standard TF-IDF because BM25 incorporates term saturation and document-length normalization.
**Verdict: REJECTED.** TF-IDF significantly *outperforms* BM25 — the
opposite direction — on P@10 (p=0.017), Recall@100 (p=0.010), and nDCG@10
(p=0.030); n=323, paired bootstrap.

**H2.** Biomedical dense retrieval will outperform a general-purpose embedding system on biomedical queries.
**Verdict: NOT SUPPORTED.** No metric shows a significant difference
between BGE and MedCPT (all p>=0.12, n=323). This means "no significant
evidence of a difference," not "proven equal" — absence of evidence is not
evidence of absence.

**H3.** Hybrid BM25 + MedCPT retrieval will outperform either retrieval method individually because lexical and semantic evidence are complementary.
**Verdict: NOT SUPPORTED for the MedCPT-vs-Hybrid comparison actually
tested** (the five comparisons Section 16 of the project spec names
explicitly do not include a direct BM25-vs-Hybrid test). MedCPT
significantly *beats* Hybrid RRF on Recall@100 (p=0.040, opposite the
predicted direction); no significant difference on P@10/MAP/MRR@10/nDCG@10.

**H4.** Cross-encoder reranking will improve top-ranked effectiveness, especially nDCG@10, while increasing latency.
**Verdict: PARTIALLY SUPPORTED.** Latency increase is large and
unambiguous (direct measurement). The nDCG@10 improvement H4 specifically
emphasizes is the best point estimate across all six models (0.3731) but
is **not statistically significant** (p=0.194, n=323). P@10 *does* improve
significantly (p=0.015).

## 5. Methodology

### 5.1 TF-IDF ✅ M2 complete

Scikit-learn `TfidfVectorizer` — sublinear term frequency, smoothed IDF, L2
normalization — with cosine similarity for ranking (`configs/tfidf.yaml`).
Educational validation against hand-computed TF/IDF examples is included in
`tests/test_tfidf.py` to confirm the production implementation matches the
textbook formulas it is meant to embody. Real test-split results (n=323
queries): P@10=0.2167, Recall@100=0.2372, MAP=0.1372, MRR@10=0.5062,
nDCG@10=0.3050 (`results/metrics/tfidf.json`).

### 5.2 BM25 ✅ M2 complete

Okapi BM25 with `k1=1.2, b=0.75` as documented initial values (Robertson &
Zaragoza, 2009), implemented transparently in `src/biomedical_ir/bm25.py`
so term-saturation and length-normalization behavior are inspectable rather
than hidden behind a third-party black box; cross-checked against
`rank_bm25.BM25Okapi` to floating-point precision. `configs/bm25.yaml` has
`tuning.enabled: false` for this milestone, so k1/b are used frozen at
their literature defaults with no dev-split search performed. Real
test-split results (n=323 queries): P@10=0.2071, Recall@100=0.2295,
MAP=0.1333, MRR@10=0.4939, nDCG@10=0.2954 (`results/metrics/bm25.json`).
On these real numbers TF-IDF's point estimates are numerically higher than
BM25's on every reported metric — the opposite direction from H1 — reported
as-is without tuning against the test set; whether this is statistically
meaningful is left to M7's paired significance testing, so H1 is neither
confirmed nor rejected here.

### 5.3 BGE (general dense retrieval) ✅ M3 complete

`BAAI/bge-base-en-v1.5`, CLS pooling, L2-normalized embeddings, retrieval
instruction prefix on queries only — see `docs/models.md` for the verified
model-card details and `configs/bge.yaml`. Real test-split results (n=323
queries): P@10=0.2796, Recall@100=0.3368, MAP=0.1831, MRR@10=0.5556,
nDCG@10=0.3712 (`results/metrics/bge.json`). BGE's point estimates exceed
both lexical baselines on every metric — the direction RQ2 asks about — but
whether that difference is significant is left to M7.

### 5.4 MedCPT (biomedical dense retrieval) ✅ M4 complete

`ncbi/MedCPT-Query-Encoder` + `ncbi/MedCPT-Article-Encoder`, CLS pooling, no
normalization, dot-product similarity, articles encoded as `[title, text]`
pairs — see `docs/models.md` and `configs/medcpt.yaml`. Real test-split
results (n=323 queries): P@10=0.2697, Recall@100=0.3488, MAP=0.1824,
MRR@10=0.5487, nDCG@10=0.3654 (`results/metrics/medcpt.json`). MedCPT beats
both lexical baselines on every metric but is essentially tied with BGE
(MedCPT ahead on Recall@100, BGE ahead on P@10/MAP/MRR@10/nDCG@10, all
small margins) — H2 is not straightforwardly supported by these raw point
estimates; significance testing is left to M7.

### 5.5 Reciprocal Rank Fusion ✅ M5 complete

`RRF(d) = Σ_i 1 / (k + rank_i(d))` over BM25 and MedCPT rankings, k=60
default (configurable, `configs/hybrid.yaml`). Chosen over raw score
summation specifically because BM25 and dot-product scores are not on
comparable scales — see `docs/architecture.md`. Real test-split results
(n=323 queries): P@10=0.2598, Recall@100=0.3389, MAP=0.1809, MRR@10=0.5678,
nDCG@10=0.3620 (`results/metrics/hybrid_rrf.json`). Hybrid wins P@1/MRR/MRR@10
(all highest of the five models run so far) but does not beat BGE/MedCPT
individually on P@10/Recall@100/MAP/nDCG@10 — H3 is only partially, not
uniformly, supported by these raw numbers.

### 5.6 Cross-Encoder Reranking ✅ M6 complete

`ncbi/MedCPT-Cross-Encoder` reranks the top candidates from the hybrid RRF
ranking (`configs/reranker.yaml`, candidate pool sizes 20/50/100 tested as
ablation A6). Full-corpus cross-encoder scoring is treated as a separate,
explicitly-labeled efficiency experiment, not the default pipeline. Real
test-split results at the default pool (50): P@10=0.2765, MAP=0.1760\*,
MRR@10=0.5670, **nDCG@10=0.3731** (`results/metrics/hybrid_reranked.json`)
— the highest nDCG@10 of all six models, directly consistent with H4.
\*MAP/Recall@100 are capped by the candidate pool (mechanically confirmed
via the A6 ablation, not a relevance-quality regression) — see
`docs/models.md` and `results/tables/main_results.md` for the full
mechanism and pool sweep.
