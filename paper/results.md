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

**Update (M7): this difference is statistically significant.** Paired
bootstrap testing (Section 9, below) confirms TF-IDF significantly
outperforms BM25 on P@10 (p=0.017), Recall@100 (p=0.010), and nDCG@10
(p=0.030) — **H1 is REJECTED**, not merely contradicted on raw numbers.

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
effectiveness compared with traditional lexical methods?"). **Update (M7):
confirmed significant.** BM25 vs. BGE is significant on all five primary
metrics (p<0.005 each) — the strongest, most robust finding in the whole
study. RQ2 is answered affirmatively for the lexical-vs-dense contrast,
with statistical support.

## MedCPT (M4, real numbers)

Computed identically on Apple M1 Pro (MPS). Full metric set:
`results/metrics/medcpt.json`. Run artifact: `results/runs/medcpt.trec`.
Manifest: `results/manifests/exp-medcpt-001.json`.

| Model | P@10 | Recall@100 | MAP | MRR@10 | nDCG@10 | Latency (ms/query) |
|---|---:|---:|---:|---:|---:|---:|
| MedCPT (biomedical dense) | 0.2697 | 0.3488 | 0.1824 | 0.5487 | 0.3654 | 1.871 |

MedCPT clearly beats both lexical baselines (TF-IDF, BM25) on every metric
above (**confirmed significant by M7**: BM25 vs. MedCPT p<0.005 on all five
metrics). Against BGE specifically, however, the comparison is close rather
than a clean win either way: MedCPT leads Recall@100 (0.3488 vs. 0.3368)
and P@1 (0.4675 vs. 0.4551), while BGE leads P@10 (0.2796 vs. 0.2697), MAP
(0.1831 vs. 0.1824), MRR@10 (0.5556 vs. 0.5487), and nDCG@10 (0.3712 vs.
0.3654) — all margins are small. **Update (M7): none of these BGE-vs-MedCPT
differences reach significance (all p≥0.12) — H2 is NOT SUPPORTED.** The
two models are statistically indistinguishable on this test set at n=323.
RQ3's premise (does domain-specific training help over pure lexical
matching) is answered affirmatively and significantly relative to
TF-IDF/BM25; the domain-vs-general dense comparison specifically shows no
significant difference either way.

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
metrics this project treats as primary). **Update (M7): MedCPT vs. Hybrid
RRF, the specific comparison the project spec names, found MedCPT
significantly *beats* Hybrid RRF on Recall@100 (p=0.040) — the opposite of
H3's predicted direction — with no significant difference on P@10, MAP,
MRR@10, or nDCG@10. H3 is NOT SUPPORTED for this comparison.** (A direct
BM25-vs-Hybrid test falls outside the five comparisons the spec names
explicitly, so that half of H3 remains untested, not disproven.)

## Cross-encoder reranking (M6, real numbers)

Reranks the hybrid RRF (M5) run's top candidates with
`ncbi/MedCPT-Cross-Encoder` (`src/biomedical_ir/reranker.py`). Candidate
pool sizes 20/50/100 all run (ablation A6). Full metric sets:
`results/metrics/hybrid_reranked.json` (default pool=50) and
`results/metrics/reranker_pool_ablation.json` (all three pools). Run
artifact: `results/runs/hybrid_reranked.trec`. Manifest:
`results/manifests/exp-reranker-001.json`.

| Pool | P@10 | Recall@100 | MAP | MRR@10 | nDCG@10 | Reranking latency (ms/query) |
|---:|---:|---:|---:|---:|---:|---:|
| 20 | 0.2622 | 0.2174 | 0.1586 | 0.5661 | 0.3640 | 765.4 |
| **50 (default)** | 0.2765 | 0.2782 | 0.1760 | 0.5670 | **0.3731** | 1941.6 |
| 100 | 0.2690 | 0.3389 | 0.1846 | 0.5668 | 0.3664 | 3918.1 |

Reranking at the default pool achieves nDCG@10 = 0.3731 — the highest
nDCG@10 of all six models in this study (hybrid RRF 0.3620, BGE 0.3712,
MedCPT 0.3654), directionally consistent with **H4**'s specific claim
("cross-encoder reranking will improve top-ranked effectiveness, especially
nDCG@10"). Latency increased dramatically and unambiguously, also as H4
predicted: reranking alone adds ~1941.6 ms/query on Apple M1 Pro (MPS) —
not representative of GPU-optimized production latency, but a real
measurement on the hardware this project ran on (`docs/reproducibility.md`).
**Update (M7): this nDCG@10 improvement is NOT statistically significant**
(paired bootstrap vs. hybrid RRF: p=0.194, n=323) — the best point estimate
in the study does not clear conventional significance here. P@10 *does*
improve significantly (p=0.015). See Section 9 below for the full test.

**Important methodological caveat, reported rather than hidden:** MAP
(0.1760) and Recall@100 (0.2782) both *decreased* relative to hybrid RRF
(MAP 0.1809, Recall@100 0.3389) at the default pool. This is **not**
evidence the reranker judges relevance worse — it is a mechanical
consequence of the candidate-pool cap: a cross-encoder can only reorder the
candidates it is given, so Recall@k for k exceeding the pool size is
identical to Recall@pool_size by construction (verified exactly: pool=20's
Recall@20/50/100 are all 0.2174; pool=50's Recall@50/100 are both 0.2782;
pool=100's Recall@100, 0.3389, matches hybrid RRF's own Recall@100 to five
decimal places, since reordering an unchanged 100-document set cannot
change how many relevant documents it contains). At pool=100 — no
candidate-pool disadvantage relative to hybrid RRF — MAP does exceed hybrid
RRF's (0.1846 vs. 0.1809), while nDCG@10 (0.3664) is still below the
pool=50 result, so effectiveness vs. pool size is genuinely non-monotonic
here rather than simply "bigger pool always better."

**Revised H4 verdict (see Statistical Analysis, below): partially
supported.** Latency increase is unambiguous. The nDCG@10 improvement is
the best point estimate in the study but is not statistically significant.

# 9. Statistical Analysis

All comparisons: paired bootstrap (`src/biomedical_ir/statistics.py`,
n_resamples=10000, seed=42), query-level, n=323. Full table:
`results/tables/statistical_tests.md` / `.json` (6 comparisons x 5 primary
metrics = 30 tests, generated by `scripts/evaluate_all.py`). Five of the six
comparisons are exactly those Section 16 of the project spec names
explicitly; TF-IDF vs. BM25 was added to directly resolve H1, which every
earlier section of this document had left open pending this step.

| Comparison | Metric | Diff (A−B) | 95% CI | p | Significant? |
|---|---|---:|---|---:|:---:|
| TF-IDF vs BM25 | P@10 | +0.0096 | [+0.0019, +0.0183] | 0.017 | **yes** |
| TF-IDF vs BM25 | Recall@100 | +0.0077 | [+0.0014, +0.0160] | 0.010 | **yes** |
| TF-IDF vs BM25 | nDCG@10 | +0.0096 | [+0.0010, +0.0183] | 0.030 | **yes** |
| TF-IDF vs BM25 | MAP | +0.0038 | [−0.0007, +0.0085] | 0.095 | no |
| TF-IDF vs BM25 | MRR@10 | +0.0123 | [−0.0107, +0.0354] | 0.295 | no |
| BM25 vs BGE | all 5 metrics | (BM25 lower on all) | — | <0.005 | **yes, all 5** |
| BM25 vs MedCPT | all 5 metrics | (BM25 lower on all) | — | <0.005 | **yes, all 5** |
| BGE vs MedCPT | all 5 metrics | (small, mixed direction) | — | ≥0.12 | no, none |
| MedCPT vs Hybrid RRF | Recall@100 | +0.0099 (MedCPT higher) | [+0.0004, +0.0199] | 0.040 | **yes** |
| MedCPT vs Hybrid RRF | P@10, MAP, MRR@10, nDCG@10 | small | — | ≥0.13 | no |
| Hybrid RRF vs Reranked | P@10 | −0.0167 (reranked higher) | [−0.0300, −0.0034] | 0.015 | **yes** |
| Hybrid RRF vs Reranked | Recall@100 | +0.0607 (reranked lower — pool cap) | [+0.0496, +0.0735] | <0.001 | **yes** |
| Hybrid RRF vs Reranked | nDCG@10 | −0.0111 (reranked higher, n.s.) | [−0.0275, +0.0061] | 0.194 | no |
| Hybrid RRF vs Reranked | MAP, MRR@10 | small | — | ≥0.29 | no |

**Per-hypothesis verdicts** (see `methodology.md` for full statements):

- **H1 — REJECTED.** TF-IDF significantly beats BM25 on P@10, Recall@100,
  nDCG@10.
- **H2 — NOT SUPPORTED.** BGE and MedCPT are statistically
  indistinguishable (all p≥0.12).
- **H3 — NOT SUPPORTED** for the comparison actually tested (MedCPT vs.
  Hybrid RRF); MedCPT significantly beats Hybrid RRF on Recall@100, the
  opposite of H3's predicted direction. A direct BM25-vs-Hybrid test was
  not run (outside the spec's named comparisons), so that half of H3
  remains untested rather than disproven.
- **H4 — PARTIALLY SUPPORTED.** Latency increase: unambiguous. Its
  flagship nDCG@10 claim: directionally correct (best estimate in the
  study) but not significant. P@10 does improve significantly.

**Study's most robust finding:** both dense retrievers (BGE, MedCPT)
significantly outperform BM25 on every one of the five primary metrics
(all p<0.005) — the classical-vs-dense gap is real and well-supported.
None of the finer "which advanced method wins" questions (biomedical vs.
general dense, hybrid vs. individual, reranked vs. not) reach significance
on their respective headline metrics at n=323 queries.
