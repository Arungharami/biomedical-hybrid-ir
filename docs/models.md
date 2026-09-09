# Models

> Status: stub — filled in as M2 (TF-IDF/BM25), M3 (BGE), M4 (MedCPT), M5
> (RRF), and M6 (cross-encoder) complete. Config decisions below are already
> finalized and verified against official sources; the *results* sections
> will be filled with real numbers as each milestone lands.

## M1 — TF-IDF

Scikit-learn `TfidfVectorizer` (sublinear TF, L2 norm, smoothed IDF) +
cosine similarity. Config: `configs/tfidf.yaml`. ⚪ Pending implementation.

## M2 — BM25

Custom transparent implementation (`k1=1.2, b=0.75` initial values, per
Robertson & Zaragoza 2009). Config: `configs/bm25.yaml`. ⚪ Pending.

## M3 — BAAI/bge-base-en-v1.5

Verified against the [official model card](https://huggingface.co/BAAI/bge-base-en-v1.5)
on 2026-09-09:
- Pooling: **CLS** (first token of `last_hidden_state`)
- Normalization: **L2-normalized** embeddings
- Query instruction: `"Represent this sentence for searching relevant passages: "` prepended to queries only, not documents
- Embedding dimension: **768**; max sequence length: **512**
- Similarity: cosine (= dot product on normalized embeddings)

Config: `configs/bge.yaml`. ⚪ Pending implementation.

## M4 — MedCPT (Query Encoder + Article Encoder)

Verified against the official model cards
([Query Encoder](https://huggingface.co/ncbi/MedCPT-Query-Encoder),
[Article Encoder](https://huggingface.co/ncbi/MedCPT-Article-Encoder)) on
2026-09-09:
- Pooling: **CLS** (`last_hidden_state[:, 0, :]`) for both encoders
- Normalization: **none** applied by the model; similarity is raw dot product
- Query max length: **64** tokens; article max length: **512** tokens
- Article input: tokenized as a **[title, text] pair**, not a manually
  concatenated string — matches `document_composition` in
  `configs/default.yaml` conceptually, but MedCPT gets the pair form
  specifically because that's what its tokenizer call expects.

Config: `configs/medcpt.yaml`. ⚪ Pending implementation.

## M5 — Hybrid (BM25 + MedCPT, RRF)

`RRF(d) = Σ 1 / (k + rank_i(d))`, k=60 default, configurable. Operates on
rank positions specifically because BM25 and dot-product scores are not on
comparable scales — see `docs/architecture.md`. Implementation:
`src/biomedical_ir/fusion.py`. ⚪ Pending.

## M6 — MedCPT Cross-Encoder reranking

Verified against the [official model card](https://huggingface.co/ncbi/MedCPT-Cross-Encoder)
on 2026-09-09:
- Input: `[query, article]` pairs, tokenized jointly; `article` is the
  document's title and text joined as `"{title}. {text}"` (the join
  convention used in MedCPT's own reference code)
- Output: a single raw logit per pair (higher = more relevant); no sigmoid
  applied for ranking
- Max sequence length: 512

Candidate pool sizes tested: 20, 50, 100 (default 50). Config:
`configs/reranker.yaml`. ⚪ Pending.
