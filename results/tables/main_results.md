# Main results (NFCorpus, test split, n=323 queries)

> Generated from `results/metrics/{tfidf,bm25,bge,medcpt,hybrid_rrf,hybrid_reranked}.json`
> (M2-M6; all six models complete) -- no number below is fabricated or estimated in
> advance of its actual run. Metrics computed with `pytrec_eval` against
> `data/raw/nfcorpus/qrels_test.json`; see `src/biomedical_ir/evaluation.py`
> for the exact measure definitions and graded-relevance handling.
> Latency = mean top-100 retrieval wall-clock time per query, from each
> run's `timing.latency_ms_per_query` (TF-IDF/BM25: CPU; BGE: Apple M1 Pro
> MPS, query-side encoding + FAISS search only, corpus encoding excluded).

| Model | P@10 | Recall@100 | MAP | MRR@10 | nDCG@10 | Latency (ms/query) |
|---|---:|---:|---:|---:|---:|---:|
| TF-IDF | 0.2167 | 0.2372 | 0.1372 | 0.5062 | 0.3050 | 3.631 |
| BM25 (k1=1.2, b=0.75) | 0.2071 | 0.2295 | 0.1333 | 0.4939 | 0.2954 | 2.155 |
| BGE (general dense) | 0.2796 | 0.3368 | 0.1831 | 0.5556 | 0.3712 | 2.678 |
| MedCPT (biomedical dense) | 0.2697 | 0.3488 | 0.1824 | 0.5487 | 0.3654 | 1.871 |
| BM25 + MedCPT (RRF) | 0.2598 | 0.3389 | 0.1809 | 0.5678 | 0.3620 | 4.069 |
| Hybrid + MedCPT Cross-Encoder Reranker (pool=50) | 0.2765 | 0.2782\* | 0.1760\* | 0.5670 | **0.3731** | 1945.6 |

\* **Recall@100 and MAP for the reranked row are capped by the candidate
pool (50), not directly comparable to the other rows' true top-100
ranking.** A cross-encoder can only reorder the candidates it is given; with
pool=50 the reranked run never contains more than 50 documents per query,
so Recall@100 == Recall@50 exactly (0.2782 both) by construction. Verified
mechanistically in the pool ablation below: pool=100's Recall@100 (0.3389)
exactly equals hybrid RRF's own Recall@100 (0.3389) — reordering an
unchanged 100-document set cannot change how many relevant documents are
present in it. See the M6 observation below for the honest read.

## M2 observation (raw numbers only, no significance claim)

On this run, TF-IDF's point estimates are numerically higher than BM25's on
every reported metric (e.g. nDCG@10: TF-IDF 0.3050 vs. BM25 0.2954; MAP:
0.1372 vs. 0.1333) -- the opposite direction from H1 ("BM25 will outperform
standard TF-IDF"). This is reported as-is; no parameter was tuned against
the test set to change it (`configs/bm25.yaml` uses the frozen literature
defaults k1=1.2, b=0.75, `tuning.enabled: false`). Whether this difference
is statistically meaningful is **not** evaluated here -- paired
significance testing across all model pairs is M7's job
(`src/biomedical_ir/statistics.py`, not yet implemented). H1 remains an
open hypothesis, not confirmed or rejected, until that test runs.

## M3 observation (raw numbers only, no significance claim)

BGE's point estimates exceed both lexical baselines on every reported
metric (nDCG@10: BGE 0.3712 vs. TF-IDF 0.3050 vs. BM25 0.2954; MAP: BGE
0.1831 vs. TF-IDF 0.1372). This is consistent with the *direction* RQ2 asks
about (does dense retrieval improve over lexical methods), but again no
significance test has been run against these specific numbers -- that is
M7's job. RQ2 is not considered answered by this milestone alone.

## M4 observation (raw numbers only, no significance claim)

MedCPT's point estimates are, on this run, essentially tied with BGE rather
than clearly ahead of it: MedCPT wins on Recall@100 (0.3488 vs. 0.3368) and
P@1 (0.4675 vs. 0.4551, not shown in the primary table above), while BGE
wins on P@10 (0.2796 vs. 0.2697), MAP (0.1831 vs. 0.1824), MRR@10 (0.5556
vs. 0.5487), and nDCG@10 (0.3712 vs. 0.3654) -- all differences are small.
This does **not** straightforwardly support H2 ("biomedical dense retrieval
will outperform a general-purpose embedding system") on raw point estimates
alone; MedCPT does clearly beat both lexical baselines (TF-IDF, BM25) on
every metric, which is consistent with RQ3's premise that domain-specific
training helps over lexical matching, just not decisively over a strong
general-purpose dense baseline here. As always, no significance test has
been run -- H2 and RQ3 remain open until M7.

## M5 observation (raw numbers only, no significance claim)

Hybrid RRF (BM25 + MedCPT, k=60) fuses the already-computed M2/M4 runs
(`results/runs/{bm25,medcpt}.trec`); one real, worth-flagging BM25 property
surfaced doing this: 25 of 323 test queries (7.7%) -- e.g. `PLAIN-1008`
"deafness", `PLAIN-1098` "eggnog", `PLAIN-1214` "Fosamax" -- share literally
zero vocabulary with any document after preprocessing, so BM25 returns an
empty ranked list for them entirely (not a bug: BM25 only scores documents
sharing >=1 query term, per `src/biomedical_ir/bm25.py`; this is the classic
vocabulary-mismatch problem lexical retrieval is known for, and part of the
motivation for RQ2/RQ4). `fuse_runs` handles this correctly -- those 25
queries still appear in the fused output via MedCPT's contribution alone
(the union of query IDs across component runs, not the intersection).

Hybrid's results are mixed relative to the individual retrievers, not a
clean win across the board:

- **Hybrid wins:** P@1 (0.4799, highest of all five models so far), MRR
  (0.5736) and MRR@10 (0.5678, both highest of all five) -- consistent with
  H3's premise that lexical and semantic evidence are complementary,
  specifically for getting *a* relevant document ranked very early.
- **Hybrid does not win:** P@10 (0.2598, below both BGE 0.2796 and MedCPT
  0.2697), Recall@100 (0.3389, below MedCPT's 0.3488, though above BGE's
  0.3368), MAP (0.1809, below both BGE 0.1831 and MedCPT 0.1824), and
  nDCG@10 (0.3620, below both BGE 0.3712 and MedCPT 0.3654).

So **H3 ("hybrid retrieval will outperform either method individually") is
only partially, not uniformly, supported by these raw point estimates** --
true for rank-of-first-relevant-document metrics (P@1, MRR, MRR@10), not
true for the metrics this project treats as primary (P@10, Recall@100, MAP,
nDCG@10). Reported exactly as observed; no significance test has been run
on any of these comparisons, and RQ4 remains open pending M7.

Latency here is deliberately reported end-to-end (BM25 retrieval + MedCPT
retrieval + RRF fusion, `4.069 ms/query`) rather than fusion-time-only
(`0.0425 ms/query`), since a real hybrid query genuinely pays both component
retrievers' cost -- see `results/metrics/hybrid_rrf.json -> timing` for both
numbers and the exact breakdown.

## M6 observation (raw numbers only, no significance claim)

Reranks the hybrid RRF (M5) run's top candidates with
`ncbi/MedCPT-Cross-Encoder` (`src/biomedical_ir/reranker.py`). Candidate
pool sizes 20/50/100 were all run (ablation A6):

| Pool | P@10 | Recall@10 | Recall@20 | Recall@50 | Recall@100 | MAP | MRR@10 | nDCG@10 | Reranking latency |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 0.2622 | 0.1811 | 0.2174 | 0.2174 | 0.2174 | 0.1586 | 0.5661 | 0.3640 | 765.4 ms/query |
| **50 (default)** | **0.2765** | 0.1895 | 0.2291 | 0.2782 | 0.2782 | 0.1760 | 0.5670 | **0.3731** | 1941.6 ms/query |
| 100 | 0.2690 | 0.1858 | 0.2269 | 0.2906 | 0.3389 | 0.1846 | 0.5668 | 0.3664 | 3918.1 ms/query |

(Recall@k for k > pool size is identical to Recall@pool within each row --
mechanically expected, not a bug: a reranker cannot recover documents it
was never given as candidates. Confirmed exactly: pool=100's Recall@100
(0.3389) equals hybrid RRF's own Recall@100 to five decimal places.)

**At the default pool (50), reranking achieves nDCG@10 = 0.3731 -- the
highest nDCG@10 of all six models in this study** (vs. hybrid RRF 0.3620,
BGE 0.3712, MedCPT 0.3654), directionally consistent with **H4**'s specific
prediction ("cross-encoder reranking will improve top-ranked effectiveness,
especially nDCG@10"). Latency also increased dramatically as H4 predicted:
reranking-only adds ~1941.6 ms/query on top of hybrid RRF's ~4.1 ms/query
(measured on Apple M1 Pro MPS -- not representative of GPU-optimized
production latency; see `docs/reproducibility.md`).

**UPDATE from M7's significance test (`results/tables/statistical_tests.md`):
the nDCG@10 improvement above is NOT statistically significant** (paired
bootstrap, hybrid RRF vs. hybrid+reranker, nDCG@10: diff=-0.0111,
p=0.1944, n=323) -- this correction supersedes any earlier framing of the
nDCG@10 result as a confirmed "headline finding"; it was, and remains,
the best raw point estimate in the study, but that alone does not establish
significance at this sample size. What IS significant: P@10 improves with
reranking (diff=-0.0167 hybrid RRF vs. reranked, i.e. reranked higher,
p=0.0150), and Recall@100 changes significantly in the direction explained
by the pool-cap artifact above (p<0.0001). MAP and MRR@10 show no
significant difference.

**However, MAP and Recall@100 both DECREASED relative to hybrid RRF**
(MAP: 0.1760 vs. 0.1809; Recall@100: 0.2782 vs. 0.3389) at the default pool.
This is **not** evidence the reranker judges relevance worse -- it is
mechanically explained by the candidate-pool cap above: hybrid RRF's own
top-100 ranking naturally has more room to accumulate recall than a
reranker restricted to reordering only its top 50 candidates. At pool=100
(no candidate-pool disadvantage vs. hybrid RRF), MAP actually improves to
0.1846 (vs. hybrid RRF's 0.1809) while nDCG@10 (0.3664) is still below the
pool=50 result -- suggesting the effectiveness/pool-size relationship is
genuinely non-monotonic here, not simply "bigger pool always better."

**Revised H4 verdict after M7's significance test: PARTIALLY supported.**
The latency increase is unambiguous, large, and requires no significance
test (it is a direct measurement). The specific nDCG@10 claim is the best
point estimate in the study but is **not statistically significant**
(p=0.194) -- so H4 is not confirmed on its most emphasized metric. P@10
does improve significantly (p=0.015), which is genuine partial support for
"reranking improves top-ranked effectiveness" in general, just not
specifically via nDCG@10 at conventional significance on n=323 queries.

---

## M7 — Statistical Analysis (paired bootstrap, real numbers)

See `results/tables/statistical_tests.md` / `.json` for the full table (6
comparisons x 5 metrics = 30 tests, paired bootstrap, n_resamples=10000,
seed=42, `src/biomedical_ir/statistics.py`). Per-hypothesis verdicts:

- **H1 (BM25 will outperform TF-IDF) -- REJECTED.** TF-IDF significantly
  outperforms BM25 on P@10 (p=0.017), Recall@100 (p=0.010), and nDCG@10
  (p=0.030); MAP and MRR@10 point the same direction but are not
  significant (p=0.095, p=0.295). This directly contradicts H1 with
  statistical support, not just a raw-number observation.
- **H2 (MedCPT will outperform BGE) -- NOT SUPPORTED.** No metric shows a
  significant difference between BGE and MedCPT (all p >= 0.12). The two
  are statistically indistinguishable on this test set at this sample size.
- **H3 (Hybrid will outperform BM25 and MedCPT individually) -- NOT
  SUPPORTED for the MedCPT comparison actually tested.** MedCPT
  significantly *beats* Hybrid RRF on Recall@100 (p=0.040, opposite the
  predicted direction); no significant difference on P@10, MAP, MRR@10, or
  nDCG@10. (A direct BM25-vs-Hybrid-RRF test was not run -- it is outside
  the five comparisons Section 16 of the project spec names explicitly --
  so H3's other half is untested, not merely unsupported.)
- **H4 (Reranking will improve nDCG@10, increase latency) -- PARTIALLY
  SUPPORTED.** Latency increase: unambiguous (direct measurement, no test
  needed). nDCG@10 improvement: **not significant** (p=0.194) despite being
  the best point estimate in the study. P@10 *does* improve significantly
  (p=0.015).

**What's confirmed statistically, not just directionally:** both dense
models (BGE, MedCPT) significantly outperform BM25 on every one of the five
primary metrics (all p<0.005) -- this is the study's most robust finding.
Beyond classical-vs-dense, none of the "which advanced method is better"
questions (biomedical vs. general dense; hybrid vs. individual; reranked
vs. not) reach significance on their headline metrics at n=323 queries.
