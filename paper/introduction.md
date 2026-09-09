# 1. Introduction

Biomedical search occupies a distinctive position in information retrieval:
queries range from precise technical terminology (drug names, gene
symbols, exact clinical vocabulary) to layperson paraphrases of health
concerns, while the target documents are typically expert-authored
scientific literature. Classical lexical retrieval (TF-IDF, BM25) handles
exact terminology well but is brittle to vocabulary mismatch — a
layperson's "salmon" and a paper's "Atlantic salmon" overlap trivially, but
a synonym or paraphrase can defeat lexical matching entirely. Dense
retrieval, whether general-purpose or trained on biomedical text
specifically, promises to bridge that gap through learned semantic
similarity, at the cost of transparency, compute, and — as this study's
results show — not always a clean win.

NFCorpus (Boteva et al., 2016) is a natural testbed for this tension: it
pairs layperson nutrition/health queries drawn from NutritionFacts.org with
graded relevance judgments against PubMed-indexed scientific articles,
released in BEIR's (Thakur et al., 2021) standardized zero-shot evaluation
format. This project builds a complete, reproducible pipeline on NFCorpus
comparing six retrieval systems — TF-IDF, BM25, BGE (general dense),
MedCPT (biomedical dense), a BM25+MedCPT hybrid via Reciprocal Rank Fusion,
and that hybrid reranked by a biomedical cross-encoder — under one shared
evaluation protocol, one qrels set (train/dev/test splits with dev-only
tuning, never test-set leakage), and formal paired significance testing at
the query level.

## Contribution

The primary contribution is not a novel algorithm but a controlled,
honestly-reported empirical comparison: every model choice (pooling,
normalization, instruction prefixes, input formats) is verified against
official model cards rather than assumed; every reported number is backed
by a real experiment with a corresponding manifest recording its exact
configuration, environment, and runtime; and — critically — every
hypothesis stated before the experiments ran (H1-H4, Section 3) is
resolved with a real significance test rather than left as a plausible
narrative built on raw point estimates alone. Several of this study's
findings run counter to textbook expectation (Section 8-9): TF-IDF
significantly beats BM25 here, MedCPT does not significantly beat a
general-purpose embedding model, and a hybrid retriever's best-known
raw-number improvement (cross-encoder reranking's nDCG@10 gain) does not
clear conventional statistical significance at this sample size. Reporting
these honestly, rather than smoothing them into the expected narrative, is
itself part of the contribution — see Section 15 of the accompanying
project specification's scientific-integrity requirement, which this
project treats as load-bearing rather than aspirational.

## Research questions and organization

Sections 3-5 state the six research questions (RQ1-RQ6) and four
hypotheses (H1-H4) this study tests, and the methodology behind each of
the six models. Section 6-7 describe the experimental setup and evaluation
metrics. Sections 8-11 report results, statistical analysis, error
analysis, and efficiency analysis — all against real data, with `Pending`
used literally for anything not yet run (none remains, as of this
writing). Sections 12-15 discuss, interpret, and honestly limit the
findings' scope.
