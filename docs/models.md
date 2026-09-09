# Models

> Status: M2 (TF-IDF/BM25) complete with real artifacts; M3 (BGE), M4
> (MedCPT), M5 (RRF), and M6 (cross-encoder) still pending. Config decisions
> below are finalized and verified against official sources; the *results*
> sections are filled with real numbers as each milestone lands.

## M1 — TF-IDF ✅ Complete

Scikit-learn `TfidfVectorizer` (sublinear TF, L2 norm, smoothed IDF) +
cosine similarity, over the lexical pipeline in
`src/biomedical_ir/preprocessing.py` (unicode NFKC, lowercase, `\w+`
tokenizer, no stopword removal). Implementation: `src/biomedical_ir/tfidf.py`.
Config: `configs/tfidf.yaml`. Real test-split (n=323) results, from
`results/metrics/tfidf.json`:

| P@10 | Recall@100 | MAP | MRR@10 | nDCG@10 | Latency |
|---:|---:|---:|---:|---:|---:|
| 0.2167 | 0.2372 | 0.1372 | 0.5062 | 0.3050 | 3.631 ms/query |

## M2 — BM25 ✅ Complete

Custom transparent implementation (`src/biomedical_ir/bm25.py`), classical
Robertson/Sparck-Jones IDF with +0.5 smoothing (no +1 inside the log --
documented precisely in the module docstring since conventions differ),
`k1=1.2, b=0.75` frozen initial values per Robertson & Zaragoza (2009);
`configs/bm25.yaml -> bm25.tuning.enabled` is `false` for this milestone, so
no dev-split grid search was run. Verified to match the third-party
`rank_bm25.BM25Okapi` to floating-point precision on positive-idf query
terms (`tests/test_bm25.py::TestCrossCheckAgainstRankBm25`). Config:
`configs/bm25.yaml`. Real test-split (n=323) results, from
`results/metrics/bm25.json`:

| P@10 | Recall@100 | MAP | MRR@10 | nDCG@10 | Latency |
|---:|---:|---:|---:|---:|---:|
| 0.2071 | 0.2295 | 0.1333 | 0.4939 | 0.2954 | 2.155 ms/query |

On this real run, TF-IDF's point estimates are numerically higher than
BM25's on every metric above -- the opposite direction from H1. This is
reported as a raw observation only; no significance test has been run yet
(that is M7's job), so H1 is neither confirmed nor rejected by this
milestone. See `results/tables/main_results.md` for further discussion.

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
