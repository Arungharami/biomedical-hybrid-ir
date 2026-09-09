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

### 5.1 TF-IDF

Scikit-learn `TfidfVectorizer` — sublinear term frequency, smoothed IDF, L2
normalization — with cosine similarity for ranking (`configs/tfidf.yaml`).
Educational validation against hand-computed TF/IDF examples is included in
`tests/test_tfidf.py` (⚪ pending M2) to confirm the production implementation
matches the textbook formulas it is meant to embody.

### 5.2 BM25

Okapi BM25 with `k1=1.2, b=0.75` as documented initial values (Robertson &
Zaragoza, 2009), implemented transparently in `src/biomedical_ir/bm25.py`
(⚪ pending M2) so term-saturation and length-normalization behavior are
inspectable rather than hidden behind a third-party black box. Any parameter
tuning is dev-only (Section 4).

### 5.3 BGE (general dense retrieval)

`BAAI/bge-base-en-v1.5`, CLS pooling, L2-normalized embeddings, retrieval
instruction prefix on queries only — see `docs/models.md` for the verified
model-card details and `configs/bge.yaml`.

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
