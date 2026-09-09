# 8. Results

M2 (TF-IDF, BM25), M3 (BGE), and M4 (MedCPT) are complete with real
artifacts; M5-M6 (hybrid RRF, cross-encoder reranking) have not run yet, so
every corresponding cell in the main results table still reads `Pending`
(Section 15 of the project spec / the root README's Experiment status
table). No metric below is estimated or fabricated in advance of its actual
run.

## TF-IDF and BM25 (M2, real numbers)

Computed with `pytrec_eval` against `data/raw/nfcorpus/qrels_test.json`
(test split, n=323 queries with qrels). Full metric sets:
`results/metrics/tfidf.json`, `results/metrics/bm25.json`. Run artifacts:
`results/runs/{tfidf,bm25}.trec`. Manifests:
`results/manifests/exp-{tfidf,bm25}-001.json`.

| Model | P@10 | Recall@100 | MAP | MRR@10 | nDCG@10 | Latency (ms/query) |
|---|---:|---:|---:|---:|---:|---:|
| TF-IDF | 0.2167 | 0.2372 | 0.1372 | 0.5062 | 0.3050 | 3.631 |
| BM25 (k1=1.2, b=0.75) | 0.2071 | 0.2295 | 0.1333 | 0.4939 | 0.2954 | 2.155 |

On this run, TF-IDF's point estimates are numerically higher than BM25's on
every metric shown here (e.g. nDCG@10: 0.3050 vs. 0.2954; MAP: 0.1372 vs.
0.1333) — the opposite direction from H1 ("BM25 will outperform standard
TF-IDF because BM25 incorporates term saturation and document-length
normalization"). This is reported factually, as computed, with no parameter
tuned against the test set to change it (`configs/bm25.yaml` uses the frozen
literature defaults k1=1.2, b=0.75, `tuning.enabled: false`).

**No significance claim is made here.** Whether this TF-IDF/BM25 difference
is statistically meaningful requires paired significance testing at the
query level (`src/biomedical_ir/statistics.py`), which is explicitly an M7
deliverable and has not run yet. H1 therefore remains an open hypothesis —
neither confirmed nor rejected — pending that test.

## BGE (M3, real numbers)

Computed identically (same test qrels, same `pytrec_eval` protocol) on
Apple M1 Pro (MPS). Full metric set: `results/metrics/bge.json`. Run
artifact: `results/runs/bge.trec`. Manifest: `results/manifests/exp-bge-001.json`.

| Model | P@10 | Recall@100 | MAP | MRR@10 | nDCG@10 | Latency (ms/query) |
|---|---:|---:|---:|---:|---:|---:|
| BGE (general dense) | 0.2796 | 0.3368 | 0.1831 | 0.5556 | 0.3712 | 2.678 |

Latency here is query-side only (query encoding + FAISS search); corpus
encoding (3,633 docs, 120.3s) is a one-time offline cost tracked separately
in the manifest, not part of per-query latency.

BGE's point estimates exceed both TF-IDF and BM25 on every metric shown
(e.g. nDCG@10: BGE 0.3712 vs. TF-IDF 0.3050 vs. BM25 0.2954) — the direction
RQ2 asks about ("Does dense semantic retrieval improve retrieval
effectiveness compared with traditional lexical methods?"). **No
significance claim is made here** for the same reason as above: paired
testing is an M7 deliverable. RQ2 is not considered answered by this
milestone alone.

## MedCPT, hybrid RRF, cross-encoder reranking

⚪ **Pending.** These milestones (M4–M6) have not run. See the root README's
Experiment status table for current milestone status.
