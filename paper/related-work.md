# 2. Related Work

## 2.1 Classical Information Retrieval

Classical IR represents documents and queries as sparse vectors over a
term vocabulary and ranks by similarity in that space — the Vector Space
Model (Salton, Wong & Yang, 1975) is the foundational formalization, and
its core idea (term overlap weighted by discriminativeness) underlies both
methods this study uses as lexical baselines.

## 2.2 TF-IDF

Term Frequency-Inverse Document Frequency weights a term by how often it
appears in a document (TF) against how rare it is across the collection
(IDF), so common words contribute little to a document's vector while
discriminative terms dominate it. This study uses scikit-learn's
production `TfidfVectorizer` implementation for the reported numbers, and
validates it against a hand-computed 3-document toy example
(`tests/test_tfidf.py`) to confirm the library matches the textbook
formula it is meant to embody (Section 6 of the accompanying spec).

## 2.3 BM25

BM25 (Robertson & Zaragoza, 2009) refines TF-IDF with two properties TF-IDF
lacks: term-frequency saturation (a term's contribution to a score
diminishes with repeated occurrence, rather than growing linearly) and
document-length normalization (a term match in a short document counts for
more than the same match in a long one). This study implements BM25
transparently from scratch (`src/biomedical_ir/bm25.py`) rather than
depending on a third-party black box, cross-checked against `rank_bm25`
for a correctness sanity check, with the classical (non-`+1`-smoothed)
Robertson/Sparck-Jones IDF formula used and documented explicitly since
conventions differ across implementations.

## 2.4 Dense Retrieval

Dense (bi-encoder) retrieval replaces sparse term-overlap vectors with
learned dense embeddings from a neural encoder, ranking by vector
similarity (typically cosine or dot product) rather than lexical overlap.
This study's general-purpose dense baseline is BGE (`bge-base-en-v1.5`,
Xiao et al., 2023's C-Pack line of embedding models), used with its
verified CLS pooling, L2-normalized embeddings, and query-only instruction
prefix.

## 2.5 Biomedical Information Retrieval

NFCorpus (Boteva et al., 2016) is this study's dataset: layperson
nutrition/health queries from NutritionFacts.org paired with graded
relevance judgments against PubMed-indexed literature, released in BEIR's
(Thakur et al., 2021) standardized zero-shot IR benchmark format — this
study verified its structure directly against the live Hugging Face Hub
rather than assuming documentation was current (`docs/dataset.md`).
MedCPT (Jin et al., 2023) is this study's biomedical-domain dense
retriever: a pair of contrastively pre-trained transformer encoders
trained on 255 million real PubMed search-log clicks, specifically built
for zero-shot biomedical semantic retrieval — the natural domain-specific
counterpart to BGE's general-purpose training.

## 2.6 Hybrid Retrieval

Hybrid retrieval combines lexical and semantic signals on the premise that
they make different, complementary errors (BM25's failures tend to be
vocabulary mismatch; a dense retriever's failures tend to be missing exact
terminology it wasn't trained to weight heavily). This study fuses BM25
and MedCPT with Reciprocal Rank Fusion (Cormack, Clarke & Buettcher, 2009),
which combines ranked lists by RANK POSITION rather than raw score — a
deliberate choice, since BM25's unbounded scores and MedCPT's raw
dot-product similarities are not on a comparable scale, and summing them
directly would implicitly and arbitrarily weight whichever retriever
happens to produce larger-magnitude numbers, not whichever is more
accurate.

## 2.7 Cross-Encoder Reranking

A cross-encoder scores a (query, document) pair jointly (both texts
attended to together, rather than encoded independently into fixed
vectors) — a strictly more expressive but far more expensive scoring
function, following the "rerank a shortlist retrieved by a cheaper method"
pattern established for neural IR by Nogueira & Cho (2019)'s BERT passage
reranker. This study uses `ncbi/MedCPT-Cross-Encoder`, the biomedical
domain-specific counterpart, to rerank the hybrid RRF run's top candidates
— never the full corpus, consistent with the standard shortlist-rerank
pattern this line of work established.

## FAISS

Approximate/exact nearest-neighbor search over dense embeddings uses FAISS
(Johnson, Douze & Jégou, 2019); this study's corpus (3,633 documents) is
small enough that exact search (`IndexFlatIP`) suffices, removing
approximation error as a confound in the effectiveness comparison between
models.
