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

## MedCPT (M4, real numbers)

Computed identically on Apple M1 Pro (MPS). Full metric set:
`results/metrics/medcpt.json`. Run artifact: `results/runs/medcpt.trec`.
Manifest: `results/manifests/exp-medcpt-001.json`.

| Model | P@10 | Recall@100 | MAP | MRR@10 | nDCG@10 | Latency (ms/query) |
|---|---:|---:|---:|---:|---:|---:|
| MedCPT (biomedical dense) | 0.2697 | 0.3488 | 0.1824 | 0.5487 | 0.3654 | 1.871 |

MedCPT clearly beats both lexical baselines (TF-IDF, BM25) on every metric
above. Against BGE specifically, however, the comparison is close rather
than a clean win either way: MedCPT leads Recall@100 (0.3488 vs. 0.3368)
and P@1 (0.4675 vs. 0.4551), while BGE leads P@10 (0.2796 vs. 0.2697), MAP
(0.1831 vs. 0.1824), MRR@10 (0.5556 vs. 0.5487), and nDCG@10 (0.3712 vs.
0.3654) — all margins are small. **H2** ("biomedical dense retrieval will
outperform a general-purpose embedding system") is therefore **not**
straightforwardly supported by these raw point estimates alone, reported
honestly rather than framed as a confirmation. RQ3's premise (does
domain-specific training help over pure lexical matching) is supported
relative to TF-IDF/BM25, but the domain-vs-general dense comparison
specifically remains open pending M7's paired significance test.

## Hybrid RRF (M5, real numbers)

Fuses the already-computed M2/M4 runs (`results/runs/{bm25,medcpt}.trec`)
via `src/biomedical_ir/fusion.py`. Full metric set:
`results/metrics/hybrid_rrf.json`. Run artifact: `results/runs/hybrid_rrf.trec`.
Manifest: `results/manifests/exp-hybrid-rrf-001.json`.

| Model | P@10 | Recall@100 | MAP | MRR@10 | nDCG@10 | Latency (ms/query) |
|---|---:|---:|---:|---:|---:|---:|
| BM25 + MedCPT (RRF, k=60) | 0.2598 | 0.3389 | 0.1809 | 0.5678 | 0.3620 | 4.069 |

Latency is reported end-to-end (BM25 retrieval + MedCPT retrieval + RRF
fusion), not fusion-time-alone (0.0425 ms/query) — a real hybrid query pays
both component retrievers' cost.

A genuine BM25 property surfaced while building this run: 25 of 323 test
queries (7.7% — e.g. "deafness", "eggnog", "Fosamax") share zero vocabulary
with any document after preprocessing, so BM25 returns an empty ranking for
them entirely (the classic lexical vocabulary-mismatch problem, part of the
motivation behind RQ2/RQ4). `fuse_runs` handles this correctly via a
union-of-query-IDs design: those queries still rank via MedCPT's
contribution alone rather than being dropped.

**H3** ("hybrid retrieval will outperform either method individually") is
**only partially supported**, not confirmed uniformly, by these raw point
estimates: hybrid wins P@1 (0.4799), MRR (0.5736), and MRR@10 (0.5678) — all
the highest values across the five models run so far — but does **not**
exceed BGE or MedCPT individually on P@10, Recall@100, MAP, or nDCG@10 (the
metrics this project treats as primary). Reported exactly as observed with
no significance test applied; RQ4 remains open pending M7.

## Cross-encoder reranking

⚪ **Pending.** M6 has not run. See the root README's Experiment status
table for current milestone status.
