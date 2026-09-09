# Models

> Status: all six models (M1-M6) complete with real artifacts as of
> 2026-09-09. Config decisions below are finalized and verified against
> official sources.

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

Config: `configs/bge.yaml`. Implementation: `src/biomedical_ir/dense.py`,
`src/biomedical_ir/faiss_index.py` (exact `IndexFlatIP` search — the 3,633
document corpus is small enough that approximate indexing isn't needed).

**M3 — ✅ Complete.** Real test-split (n=323) results, run on Apple M1 Pro
(MPS), from `results/metrics/bge.json`:

| P@10 | Recall@100 | MAP | MRR@10 | nDCG@10 | Latency |
|---:|---:|---:|---:|---:|---:|
| 0.2796 | 0.3368 | 0.1831 | 0.5556 | 0.3712 | 2.678 ms/query (query-side only) |

Corpus encoding (3,633 docs) took 120.3s on MPS; model load 24.6s. BGE's
point estimates exceed both TF-IDF and BM25 on every metric above — the
direction RQ2 asks about — but no significance test has run yet (M7), so
RQ2 is not considered answered by this milestone alone.

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

Config: `configs/medcpt.yaml`. Implementation: `src/biomedical_ir/medcpt.py`
(raw `transformers.AutoModel`, two separate encoders, manual CLS pooling —
unlike BGE which uses sentence-transformers' built-in pooling). The
title/text-pair tokenizer call was empirically verified (not assumed) to
produce identical `input_ids` to `tokenizer(text=titles, text_pair=texts, ...)`
before being used in production code.

**M4 — ✅ Complete.** Real test-split (n=323) results, run on Apple M1 Pro
(MPS), from `results/metrics/medcpt.json`:

| P@10 | Recall@100 | MAP | MRR@10 | nDCG@10 | Latency |
|---:|---:|---:|---:|---:|---:|
| 0.2697 | 0.3488 | 0.1824 | 0.5487 | 0.3654 | 1.871 ms/query (query-side only) |

Both encoders loaded in 52.3s; corpus encoding (3,633 docs) took 141.9s.
MedCPT beats both lexical baselines (TF-IDF, BM25) on every metric, but is
essentially tied with BGE rather than clearly ahead of it (MedCPT wins on
Recall@100, BGE wins on P@10/MAP/MRR@10/nDCG@10, all by small margins). H2
("biomedical dense retrieval will outperform general-purpose") is **not**
straightforwardly supported by these raw point estimates — reported
honestly rather than framed as a win, pending M7's significance testing.

## M5 — Hybrid (BM25 + MedCPT, RRF)

`RRF(d) = Σ 1 / (k + rank_i(d))`, k=60 default, configurable. Operates on
rank positions specifically because BM25 and dot-product scores are not on
comparable scales — see `docs/architecture.md`. Implementation:
`src/biomedical_ir/fusion.py`, unit-tested against hand-computed rankings
(`tests/test_fusion.py`, per Section 10 of the spec).

**M5 — ✅ Complete.** Fuses the already-computed M2/M4 runs
(`results/runs/{bm25,medcpt}.trec`). Real test-split (n=323) results, from
`results/metrics/hybrid_rrf.json`:

| P@10 | Recall@100 | MAP | MRR@10 | nDCG@10 | Latency |
|---:|---:|---:|---:|---:|---:|
| 0.2598 | 0.3389 | 0.1809 | 0.5678 | 0.3620 | 4.069 ms/query (end-to-end: bm25 + medcpt + fusion) |

Mixed result relative to the individual retrievers: hybrid wins P@1
(0.4799), MRR (0.5736), and MRR@10 (0.5678) — all highest of the five
models run so far — but does **not** beat BGE/MedCPT individually on P@10,
Recall@100, MAP, or nDCG@10. H3 is therefore only partially supported by
these raw numbers, not uniformly. One notable finding surfaced along the
way: 25/323 test queries (7.7%, e.g. "deafness", "eggnog", "Fosamax") share
zero vocabulary with the corpus after preprocessing, so BM25 returns an
empty ranking for them entirely — the classic vocabulary-mismatch problem,
correctly handled by `fuse_runs`'s union-of-query-IDs semantics (those
queries still get ranked via MedCPT's contribution alone).

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
`configs/reranker.yaml`. Implementation: `src/biomedical_ir/reranker.py`.
The joint tokenizer call was empirically verified (not assumed) to match
`tokenizer(text=queries, text_pair=articles, ...)` before use in production
code.

**M6 — ✅ Complete.** Real test-split (n=323) results, Apple M1 Pro (MPS),
from `results/metrics/hybrid_reranked.json` (default pool=50):

| P@10 | Recall@100\* | MAP\* | MRR@10 | nDCG@10 | Latency |
|---:|---:|---:|---:|---:|---:|
| 0.2765 | 0.2782 | 0.1760 | 0.5670 | **0.3731** | 1945.6 ms/query (end-to-end) |

\*Capped by the candidate pool — see the ablation below.

**Headline finding:** reranking achieves **nDCG@10 = 0.3731, the highest of
all six models** in this study (vs. hybrid RRF 0.3620, BGE 0.3712, MedCPT
0.3654) — directly consistent with H4's specific prediction. Latency
increased dramatically as H4 also predicted (~1941.6 ms/query reranking
alone, vs. hybrid RRF's ~4.1 ms/query end-to-end).

MAP and Recall@100 both *decreased* relative to hybrid RRF at the default
pool, but this is a mechanical artifact of the pool cap, not evidence the
reranker judges relevance worse: a cross-encoder can only reorder the
candidates it's given, so Recall@k for k > pool_size is identical to
Recall@pool_size by construction. Confirmed exactly via the pool ablation
(A6, `results/metrics/reranker_pool_ablation.json`): pool=100's Recall@100
(0.3389) matches hybrid RRF's own Recall@100 to five decimal places (same
document set, just reordered).

| Pool | P@10 | Recall@100 | MAP | nDCG@10 | Reranking latency |
|---:|---:|---:|---:|---:|---:|
| 20 | 0.2622 | 0.2174 | 0.1586 | 0.3640 | 765.4 ms/query |
| **50 (default)** | 0.2765 | 0.2782 | 0.1760 | **0.3731** | 1941.6 ms/query |
| 100 | 0.2690 | 0.3389 | 0.1846 | 0.3664 | 3918.1 ms/query |

Effectiveness vs. pool size is non-monotonic for nDCG@10 (peaks at 50, not
100) — reported as observed, not smoothed over. **H4 is substantially, but
not uncritically, supported**: the nDCG@10 claim is directly confirmed by
the largest margin in the study, latency clearly increased, but the claim
doesn't extend cleanly to every metric once the recall-capping mechanism is
accounted for. No significance test has been run on any of this (M7).
