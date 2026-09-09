# Main results (NFCorpus, test split, n=323 queries)

> Generated from `results/metrics/{tfidf,bm25,bge,medcpt,hybrid_rrf}.json`
> (M2, M3, M4, M5). The M6 row is `Pending` until that milestone produces a real artifact under
> `results/metrics/` -- no number below is fabricated or estimated in
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
| Hybrid + MedCPT Cross-Encoder Reranker | Pending | Pending | Pending | Pending | Pending | Pending |

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
