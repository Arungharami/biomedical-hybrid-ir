# 3. Research Questions & 5. Methodology

## 3. Research Questions

**RQ1.** How does BM25 compare with TF-IDF for biomedical retrieval on NFCorpus?

**RQ2.** Does dense semantic retrieval improve retrieval effectiveness compared with traditional lexical methods?

**RQ3.** Does a biomedical-domain retrieval model such as MedCPT outperform a general-purpose dense retrieval model?

**RQ4.** Does hybrid lexical-semantic retrieval outperform BM25 and MedCPT individually?

**RQ5.** Does biomedical cross-encoder reranking improve top-ranked retrieval effectiveness?

**RQ6.** What effectiveness/efficiency trade-offs exist among traditional, dense, hybrid, and reranked retrieval systems?

## Hypotheses

These are stated as hypotheses to be tested, not findings. They are not
reported as confirmed anywhere in this repository until the corresponding
experiment and statistical test (Section 9 below / `docs/evaluation.md`)
complete.

**H1.** BM25 will outperform standard TF-IDF because BM25 incorporates term saturation and document-length normalization.

**H2.** Biomedical dense retrieval will outperform a general-purpose embedding system on biomedical queries.

**H3.** Hybrid BM25 + MedCPT retrieval will outperform either retrieval method individually because lexical and semantic evidence are complementary.

**H4.** Cross-encoder reranking will improve top-ranked effectiveness, especially nDCG@10, while increasing latency.

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

### 5.4 MedCPT (biomedical dense retrieval)

`ncbi/MedCPT-Query-Encoder` + `ncbi/MedCPT-Article-Encoder`, CLS pooling, no
normalization, dot-product similarity, articles encoded as `[title, text]`
pairs — see `docs/models.md` and `configs/medcpt.yaml`.

### 5.5 Reciprocal Rank Fusion

`RRF(d) = Σ_i 1 / (k + rank_i(d))` over BM25 and MedCPT rankings, k=60
default (configurable, `configs/hybrid.yaml`). Chosen over raw score
summation specifically because BM25 and dot-product scores are not on
comparable scales — see `docs/architecture.md`.

### 5.6 Cross-Encoder Reranking

`ncbi/MedCPT-Cross-Encoder` reranks the top candidates from the hybrid RRF
ranking (`configs/reranker.yaml`, candidate pool sizes 20/50/100 tested as
ablation A6). Full-corpus cross-encoder scoring is treated as a separate,
explicitly-labeled efficiency experiment, not the default pipeline.
