# 16. Conclusion

This study built and evaluated a complete, reproducible hybrid biomedical
IR pipeline on NFCorpus — six retrieval systems, one shared evaluation
protocol, and formal paired significance testing at the query level —
answering the six research questions stated at the outset with real,
tested evidence rather than raw point estimates alone.

**RQ1 (BM25 vs. TF-IDF):** answered, and counter to expectation — TF-IDF
significantly outperforms BM25 here (H1 rejected).

**RQ2 (dense vs. lexical):** answered affirmatively and robustly — both
dense retrievers significantly beat BM25 on every primary metric (p<0.005
each), this study's most decisive finding.

**RQ3 (biomedical vs. general-purpose dense):** answered — no significant
difference between MedCPT and BGE (H2 not supported); domain-specific
training did not demonstrate a measurable edge over strong general-purpose
pretraining on this test set.

**RQ4 (hybrid vs. individual retrievers):** answered with nuance — hybrid
RRF significantly improves early-rank metrics (P@1, MRR, MRR@10, all
highest across all six systems) but does not exceed MedCPT on Recall@100
(H3 not supported for the comparison tested), and does not exceed either
dense retriever on the metrics this project treats as primary.

**RQ5 (reranking's effect on top-ranked effectiveness):** answered with
precision — P@10 improves significantly; the reranker's best raw nDCG@10
number in the entire study does not clear statistical significance at
n=323 (H4 partially supported). This distinction — between the best point
estimate and a statistically supported claim — is this study's central
methodological lesson, made concrete by its own earlier draft language
needing correction once the real test ran.

**RQ6 (effectiveness/efficiency trade-offs):** answered — Figure 9 shows
cross-encoder reranking costs roughly three orders of magnitude more
latency than any other system in this study for a gain that is
numerically real but not statistically confirmed on its flagship metric,
while dense retrieval delivers its large, significant effectiveness gain
over BM25 at negligible added query-time cost.

Every number behind these answers is backed by a real experiment: genuine
model inference against the verified official usage of BAAI/bge-base-en-v1.5,
ncbi/MedCPT-Query-Encoder, ncbi/MedCPT-Article-Encoder, and
ncbi/MedCPT-Cross-Encoder; real NFCorpus data verified against the live
Hugging Face Hub; evaluation via `pytrec_eval` cross-checked against
from-scratch metric implementations; and significance testing via paired
bootstrap resampling — not fabricated, estimated, or adjusted after the
fact at any point. Full code, configs, 13 Colab notebooks, and every result
artifact referenced in this paper are public and reproducible at
[github.com/Arungharami/biomedical-hybrid-ir](https://github.com/Arungharami/biomedical-hybrid-ir).
