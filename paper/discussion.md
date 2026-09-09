# 12. Discussion

## The classical-lexical-vs-dense gap is this study's clearest result

Both dense retrievers significantly and substantially outperform BM25 on
every one of the five primary metrics (p<0.005 each) — the single most
robust finding across all 30 significance tests run (`results/tables/statistical_tests.md`).
Query-level error analysis grounds this aggregate result concretely:
MedCPT recovers a relevant document BM25 misses roughly 5:1 relative to
the reverse (244 vs. 52 cases, `results/error-analysis/error_analysis.md`),
and hybrid fusion recovers far more often from BM25's failures (76 cases)
than from MedCPT's (17 cases) — consistent with BM25 being the weaker
component here, specifically because of the vocabulary-mismatch problem a
learned semantic representation is built to solve.

## BM25 did not beat TF-IDF here — a genuine, surprising result

H1 predicted BM25 would outperform TF-IDF via term-saturation and
length-normalization. The opposite happened, and significantly so (P@10
p=0.017, Recall@100 p=0.010, nDCG@10 p=0.030). We do not have a definitive
mechanistic explanation for this within the scope of this study — NFCorpus
documents vary substantially in length (scientific abstracts to full
articles) and BM25's length normalization could plausibly interact
unfavorably with that variance in ways TF-IDF's simpler weighting does
not, but this is offered as a hypothesis for future investigation, not a
confirmed mechanism. What can be said with confidence: the frozen,
literature-standard BM25 parameters used here (k1=1.2, b=0.75, never tuned
against the test set) are not tautologically superior to TF-IDF, and
reporting that plainly is more useful than assuming the textbook default
must hold.

## Domain-specific training did not significantly beat general-purpose training

H2 predicted MedCPT (trained on 255M real PubMed search-log clicks) would
outperform BGE (general-purpose) on biomedical queries. It did not, on
either metric direction: BGE leads P@10/MAP/MRR@10/nDCG@10, MedCPT leads
Recall@100/P@1, and none of the five differences are significant
(all p≥0.12). Two readings are both consistent with this: (a) BGE's
general-purpose pretraining corpus likely already contains substantial
biomedical/scientific text, narrowing the domain gap MedCPT's specialized
training was meant to close; or (b) NFCorpus's specific query style
(layperson paraphrase against expert text) may reward general semantic
matching as much as biomedical term-level precision. This study cannot
distinguish between these explanations and does not claim to — it reports
only that the two are statistically indistinguishable on this test set,
at this sample size.

## Hybrid fusion helped early-rank metrics, not the primary ones

H3 predicted hybrid RRF would outperform both BM25 and MedCPT individually.
Against MedCPT specifically (the only individual-retriever comparison the
project's evaluation protocol names), the hybrid does not win — MedCPT
significantly beats it on Recall@100 (p=0.040), the opposite of the
predicted direction. Where hybrid RRF *does* lead is P@1, MRR, and MRR@10
(all highest across all six systems), suggesting rank fusion is
specifically good at surfacing *a* relevant document very early, even when
it doesn't improve the fuller ranking quality metrics (P@10, Recall@100,
MAP, nDCG@10) this project treats as primary. This is a real, if narrower,
form of complementary-evidence benefit than H3's broad claim predicted.

## Reranking's best number in the study is not (yet) statistically distinguishable from noise

Cross-encoder reranking (pool=50) achieves nDCG@10=0.3731, numerically the
best of all six systems — but the improvement over hybrid RRF is not
significant (p=0.194, n=323). This is worth dwelling on precisely because
it is easy to overstate: this project's own earlier working notes
initially framed this number as a "headline finding" before the
significance test ran, and that framing had to be walked back once real
statistical evidence arrived (documented in `docs/models.md` and
`results/tables/main_results.md` as a correction, not silently edited
away). The lesson generalizes: a single best point estimate, however
appealing a narrative it suggests, is not evidence of a real effect until
tested — and this project's own trajectory is a concrete illustration of
that discipline actually mattering, not just a rule stated in the
abstract.

What *is* significant: P@10 improves with reranking (p=0.015), and the
reranker's error-analysis footprint (926 improved vs. 832 degraded
individual query-document pairs, `results/error-analysis/error_analysis.md`)
shows real, substantial per-query movement in both directions that
plausibly explains why the aggregate nDCG@10 effect washes out to
non-significance — the reranker is not uniformly better, it is
differently distributed.

## Efficiency

Figure 9 (`results/figures/figure9_ndcg_vs_latency.png`) makes the
trade-off's shape visually obvious: TF-IDF/BM25/BGE/MedCPT/Hybrid-RRF
cluster in a tight low-latency band (2-4 ms/query), while cross-encoder
reranking sits roughly three orders of magnitude further right
(~1942 ms/query) for a numerically small, statistically non-significant
nDCG@10 gain over hybrid RRF. On this project's hardware (Apple M1 Pro,
MPS — not representative of GPU-optimized production latency, see
`docs/reproducibility.md`), that trade-off looks unfavorable for
latency-sensitive deployment; a production system with strict latency
budgets would likely prefer hybrid RRF alone, reserving reranking for
settings where the ~2-second cost is acceptable and P@10's real, smaller,
significant gain matters specifically.
