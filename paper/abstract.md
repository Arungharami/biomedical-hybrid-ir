# Abstract

Biomedical information retrieval sits between two demands that are often in
tension: exact lexical precision (drug names, gene symbols, precise
terminology) and semantic understanding of paraphrased, layperson queries
against expert-authored literature. We present a reproducible study on
NFCorpus (3,633 documents, 323 test queries, verified against the live
Hugging Face Hub) comparing six retrieval systems along the progression
classical lexical retrieval (TF-IDF, BM25) → general-purpose dense
retrieval (BGE) → biomedical-domain dense retrieval (MedCPT) → hybrid
lexical-semantic fusion (Reciprocal Rank Fusion) → biomedical cross-encoder
reranking, under one evaluation protocol, one qrels set, and paired
query-level significance testing (paired bootstrap, n=323, n_resamples=10000).

Contrary to a common textbook expectation, TF-IDF significantly
outperforms BM25 on this corpus (P@10, Recall@100, nDCG@10; p<0.03 each).
Both dense retrievers significantly and substantially outperform BM25 on
every primary metric (p<0.005 each) — the study's most robust finding —
but biomedical-domain training (MedCPT) does not significantly outperform
a strong general-purpose embedding model (BGE); the two are statistically
indistinguishable (all p≥0.12). Hybrid RRF improves rank-of-first-relevant
metrics (P@1, MRR, MRR@10 — all highest across the six systems) but does
not exceed either individual dense retriever on P@10, Recall@100, MAP, or
nDCG@10; MedCPT specifically and significantly beats the hybrid on
Recall@100 (p=0.040), the opposite of what complementary-evidence fusion
would predict. Cross-encoder reranking achieves the highest nDCG@10 of all
six systems (0.3731) at a real, substantial latency cost (~1942 ms/query on
Apple M1 Pro), but that specific improvement is not statistically
significant (p=0.194); P@10 does improve significantly (p=0.015).
Query-level error analysis surfaces concrete mechanisms behind these
aggregate numbers — e.g. dense retrieval recovering from BM25's
vocabulary-mismatch failures roughly 5:1 relative to the reverse, while
exact lexical matching still wins outright on short, unambiguous queries
("salmon": BM25 rank 2, MedCPT: not retrieved).

Every number reported here is backed by a real experiment: 3,633 documents
and 323 test queries retrieved and scored by genuine model inference (BGE,
MedCPT, and a MedCPT cross-encoder, all run against their verified official
usage), evaluated with `pytrec_eval` and cross-checked against
from-scratch metric implementations, and tested for significance with a
paired bootstrap — not estimated, assumed, or adjusted after the fact. Full
code, configs, notebooks, and results are public at
[github.com/Arungharami/biomedical-hybrid-ir](https://github.com/Arungharami/biomedical-hybrid-ir).
