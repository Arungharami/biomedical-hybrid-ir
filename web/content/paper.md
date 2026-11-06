## Abstract

Dense retrieval is the decisive improvement for consumer-health search on NFCorpus: both dense retrievers beat BM25 on every primary metric (paired bootstrap, p < 0.005), raising nDCG@10 from 0.295 to 0.371 (BGE) and 0.365 (MedCPT). We compare six systems on the same 3,633-document corpus, 323 held-out test queries and graded qrels: TF-IDF, BM25, a general dense bi-encoder (BGE-base-en-v1.5), a biomedical bi-encoder (MedCPT), a hybrid of BM25 and MedCPT by Reciprocal Rank Fusion (RRF, k = 60), and the hybrid reranked by the MedCPT cross-encoder. Fusion gives the best MRR@10 (0.568) but not the best recall; MedCPT alone retrieves significantly more relevant documents in its top 100 (p = 0.040). Cross-encoder reranking yields the highest nDCG@10 (0.373) and a significant P@10 gain (+0.017, p = 0.015), yet its nDCG@10 gain over the hybrid is not significant (p = 0.194) and it costs about 480 times the latency. Two hypotheses fail: BM25 does not beat TF-IDF (TF-IDF is significantly better on three metrics, partly because it pads short result lists with zero-score documents and BM25’s idf turns negative for common words), and biomedical pre-training gives no measurable advantage over a strong general encoder. Rank-overlap and score-distribution analyses of the stored runs explain both the value and the limits of fusion: the two retrievers share few top-ranked documents, and their score scales differ by an order of magnitude. All results are reproducible from released code, runs and manifests.

## 1 Introduction

Consumer-health search fails most often because people and papers use different words. A user types “canker sores”; the paper judged relevant discusses “recurrent aphthous ulcers”. A user types “Fosamax”; the relevant paper says “bisphosphonate”. A purely lexical engine cannot connect these pairs, and on NFCorpus BM25 returns an empty ranking for 25 of the 323 test queries (7.7%) because no query term occurs anywhere in the corpus.

The field has answered vocabulary mismatch with dense bi-encoders, rank fusion and cross-encoder reranking. Each adds cost and complexity, and their benefits are usually reported as point estimates on large web benchmarks. This study asks whether those benefits hold, and hold significantly, on a small biomedical collection with lay queries and graded expert judgments.

We compare six systems under one protocol: the same corpus, the same 323 test queries, the same graded qrels, the same evaluator (pytrec_eval) and paired bootstrap tests at the query level. The research questions are:

1. **RQ1** How does BM25 compare with TF-IDF on NFCorpus?
2. **RQ2** Does dense retrieval improve over lexical retrieval?
3. **RQ3** Does a biomedical encoder (MedCPT) beat a general encoder (BGE)?
4. **RQ4** Does hybrid BM25 + MedCPT fusion beat each component?
5. **RQ5** Does cross-encoder reranking improve top-ranked effectiveness?
6. **RQ6** What effectiveness and efficiency trade-offs separate the systems?

Before running anything we stated four hypotheses: H1, BM25 beats TF-IDF; H2, MedCPT beats BGE; H3, the hybrid beats both components; H4, reranking improves nDCG@10 at a latency cost.

**Contributions.**

- A controlled comparison of six retrieval families with significance tests, efficiency measurements and per-query error analysis, all derived from stored runs and manifests.
- A run-level analysis of why fusion helps less than expected: BM25 and MedCPT share on average only 2.8 of their top 10 documents, and RRF imports BM25 errors as readily as BM25 successes.
- An evaluation-protocol finding: TF-IDF fills every ranking to depth 100 with zero-similarity documents while BM25 returns only matching documents, which can bias depth-dependent metrics in TF-IDF’s favour; together with negative BM25 idf weights, this qualifies the rejection of H1.
- A live demonstration system that runs the evaluated pipeline on arbitrary queries and scores judged queries against the qrels in real time.

## 2 Related work

Retrieval has moved from counting words to learning representations, and each step trades transparency and speed for robustness to wording. This study samples one point from each step.

**Lexical retrieval.** The vector space model scores documents by the cosine of TF-IDF vectors (Salton et al., 1975). BM25 grew out of the probabilistic relevance framework and adds term-frequency saturation and document-length normalization (Robertson and Zaragoza, 2009). Both rely on an inverted index and remain strong zero-shot baselines; on BEIR, BM25 beats many neural retrievers outside their training domain (Thakur et al., 2021).

**Dense bi-encoders.** Dense passage retrieval encodes queries and documents separately into vectors and ranks by inner product (Karpukhin et al., 2020). Contrastive pre-training on weakly paired text produced general encoders such as Contriever (Izacard et al., 2022) and the BGE family (Xiao et al., 2023), compared on the MTEB benchmark (Muennighoff et al., 2023). Exact and approximate vector search at scale is provided by FAISS (Johnson et al., 2019).

**Biomedical retrieval.** Domain language models such as BioBERT (Lee et al., 2020) and PubMedBERT (Gu et al., 2021) improved biomedical understanding. MedCPT trains query and article encoders, and a cross-encoder, contrastively on PubMed search logs, targeting zero-shot biomedical retrieval (Jin et al., 2023). NFCorpus pairs lay NutritionFacts.org queries with graded relevance to PubMed articles (Boteva et al., 2016).

**Hybrid retrieval and fusion.** Reciprocal Rank Fusion combines rankings using only positions and is robust without tuning (Cormack et al., 2009). Bruch et al. (2023) compare RRF with convex combinations of normalized scores and find that tuned score combinations can match or beat RRF, but need labelled data to set the weight.

**Cross-encoders and LLM reranking.** Feeding the query and document jointly through BERT gave large reranking gains (Nogueira and Cho, 2019; Lin et al., 2021). Recent work reranks with large language models, listwise or pairwise, e.g. RankGPT (Sun et al., 2023) and open models such as RankZephyr (Pradeep et al., 2023).

**Modern alternatives not evaluated here.** Learned sparse retrieval (SPLADE; Formal et al., 2021) keeps an inverted index but learns term weights and expansions. Late interaction (ColBERT; Khattab and Zaharia, 2020) keeps per-token vectors. Query and document expansion — doc2query (Nogueira et al., 2019), LLM-generated pseudo-documents in HyDE (Gao et al., 2023) and query2doc (Wang et al., 2023) — attacks vocabulary mismatch at the text level. Retrieval-augmented generation (Lewis et al., 2020) makes first-stage retrieval quality the ceiling on answer quality. Section 7 discusses which of these fit the failure modes we observe.

**Evaluation.** We follow Cranfield-style evaluation with graded nDCG (Järvelin and Kekäläinen, 2002) and query-level significance testing, for which Smucker et al. (2007) show that bootstrap, permutation and t-tests largely agree on IR data.

## 3 Methods

The pipeline sends each query through a lexical and a dense retriever in parallel, fuses their top-100 lists by rank, and lets a cross-encoder reorder the top 50. Figure 1 shows the architecture; the subsections give the exact scoring functions as implemented.

<!-- figure:architecture -->

**Figure 1.** The lexical and dense paths are independent until fusion; the only expensive query-time step is the cross-encoder.

### 3.1 Notation

Let C be the corpus of N = 3,633 documents, q a query, tf(t, d) the count of term t in document d, df(t) the number of documents containing t, |d| the length of d in tokens and avgdl the mean length. A ranking R<sub>q</sub> is an ordered list of documents; rank<sub>R</sub>(d) is the 1-based position of d in R, undefined if d is absent. All lexical models share one preprocessing: NFKC normalization, lower-casing, punctuation stripping and regex tokenization, with no stemming and no stopword removal. Lexical documents are composed as title + “ [SEP] ” + abstract.

### 3.2 TF-IDF with cosine similarity

Term weights use sublinear term frequency and smoothed idf (scikit-learn defaults), and documents are L2-normalized:

```latex
w(t,d) = \bigl(1 + \ln \mathrm{tf}(t,d)\bigr) \cdot \Bigl( \ln \frac{1 + N}{1 + \mathrm{df}(t)} + 1 \Bigr),
\qquad
s_{\text{TF-IDF}}(q,d) = \frac{\mathbf{w}_q \cdot \mathbf{w}_d}{\lVert \mathbf{w}_q \rVert \, \lVert \mathbf{w}_d \rVert}
```

This idf is always at least 1, so every shared term adds non-negative evidence. The retriever returns the 100 highest cosines, including documents whose cosine is 0 when fewer than 100 documents share a term (Section 6.3).

### 3.3 BM25

BM25 scores only documents in the postings of at least one query term:

```latex
s_{\text{BM25}}(q,d) = \sum_{t \in q} \mathrm{idf}(t) \cdot \frac{\mathrm{tf}(t,d)\,(k_1 + 1)}{\mathrm{tf}(t,d) + k_1 \bigl(1 - b + b \, \frac{|d|}{\mathrm{avgdl}}\bigr)},
\qquad
\mathrm{idf}(t) = \ln \frac{N - \mathrm{df}(t) + 0.5}{\mathrm{df}(t) + 0.5}
```

We use the textbook defaults k1 = 1.2 and b = 0.75, untuned. The saturation term caps the contribution of a repeated word at (k1 + 1) × idf, and b scales how strongly long abstracts are penalized. This idf variant (the original Robertson–Spärck Jones form, without the “+ 1” some toolkits add) is negative whenever df(t) > N/2, i.e. for words such as “the” or “of” that occur in more than 1,816 documents. Figure 2 plots both effects.

<!-- figure:saturation -->

<!-- figure:idf -->

**Figure 2.** (a) Term-frequency saturation: k1 sets how quickly repetition stops paying. (b) The two idf functions diverge for common words: BM25 subtracts evidence for terms in more than 1,816 documents, TF-IDF never does.

### 3.4 Dense bi-encoders

A bi-encoder maps query and document independently to vectors and scores by inner product:

```latex
s_{\text{dense}}(q,d) = \langle E_Q(q),\, E_D(d) \rangle, \qquad E_Q, E_D : \text{text} \to \mathbb{R}^{768}
```

**BGE-base-en-v1.5** uses one shared encoder with [CLS] pooling, prefixes queries with the instruction “Represent this sentence for searching relevant passages: ”, and L2-normalizes both vectors, so the inner product equals cosine similarity. **MedCPT** uses separate query and article encoders (queries truncated to 64 tokens; articles encoded as a (title, abstract) pair, 512 tokens), [CLS] pooling and an unnormalized dot product, as its model card specifies. Document vectors are computed once and searched exactly with FAISS IndexFlatIP; at 3,633 × 768 floats exact search costs about 2 ms per query, so no approximate index is needed and no approximation error enters the comparison.

### 3.5 Reciprocal Rank Fusion

The hybrid fuses the BM25 and MedCPT top-100 lists by rank alone:

```latex
\mathrm{RRF}(d) = \sum_{R \in \{R_{\text{BM25}},\, R_{\text{MedCPT}}\}} \frac{\mathbb{1}[d \in R]}{k + \mathrm{rank}_R(d)}, \qquad k = 60
```

Ranks are used because the raw scores are incommensurable (Section 6.1). The constant k controls how fast a document's contribution decays with depth: with k = 60 the first-ranked document earns 1/61 ≈ 0.0164 and the 10th earns 1/70 ≈ 0.0143, only 13% less, so agreement between the two lists outweighs a single first place (Figure 3). A document absent from a list receives nothing from it; queries for which BM25 returns nothing are therefore ranked by MedCPT alone.

<!-- figure:rrf -->

**Figure 3.** The larger k, the flatter the credit across ranks, so being present in both lists matters more than the exact position in either.

### 3.6 Cross-encoder reranking

The MedCPT cross-encoder reads the query and one candidate jointly, as [CLS] q [SEP] title. abstract [SEP] (maximum 512 tokens), and outputs one relevance logit:

```latex
s_{\text{CE}}(q,d) = \mathbf{w}^{\top} \, \mathrm{BERT}\bigl([q \,;\, d]\bigr)_{[\mathrm{CLS}]}
```

Every query token attends to every document token, which makes the score more precise than a dot product of two independent vectors but requires one transformer pass per (query, candidate) pair at query time. We rerank the top P = 50 RRF candidates (P = 20 and 100 in the ablation) and discard the RRF scores. A reranked list therefore contains at most P documents, which caps Recall@k for k > P.

### 3.7 Evaluation measures

NFCorpus test judgments are graded rel(d) ∈ {1, 2}; unjudged documents count as rel = 0. Binary measures treat rel ≥ 1 as relevant. For a ranking R of query q with relevant set Rel<sub>q</sub>:

```latex
\mathrm{P@}k = \frac{|R_{1..k} \cap \mathrm{Rel}_q|}{k}, \qquad
\mathrm{R@}k = \frac{|R_{1..k} \cap \mathrm{Rel}_q|}{|\mathrm{Rel}_q|}, \qquad
\mathrm{RR@}k = \frac{1}{\min\{\, i \le k : R_i \in \mathrm{Rel}_q \,\}}
```

```latex
\mathrm{AP} = \frac{1}{|\mathrm{Rel}_q|} \sum_{i : R_i \in \mathrm{Rel}_q} \mathrm{P@}i, \qquad
\mathrm{nDCG@}k = \frac{\sum_{i=1}^{k} \mathrm{rel}(R_i) / \log_2(i+1)}{\sum_{i=1}^{k} \mathrm{rel}(R^{*}_i) / \log_2(i+1)}
```

R\* is the ideal ranking (judgments sorted by grade). nDCG uses linear gain, matching trec_eval’s ndcg_cut. MAP and MRR@10 are the means of AP and RR@10 over all 323 test queries; a query with an empty ranking contributes 0. All reported values come from pytrec_eval and agree with our own implementations within floating-point tolerance.

### 3.8 Significance testing

For systems A and B with per-query scores a<sub>i</sub>, b<sub>i</sub> (i = 1..n, n = 323) we test the mean paired difference with a two-sided bootstrap (B = 10,000 resamples, seed 42):

```latex
\bar{\delta} = \frac{1}{n}\sum_{i=1}^{n} (a_i - b_i), \qquad
\bar{\delta}^{*}_b = \frac{1}{n}\sum_{i=1}^{n} \delta_{j_{b,i}}, \; j_{b,i} \sim \mathcal{U}\{1..n\}, \qquad
p = \min\Bigl(1,\; 2 \min\bigl(\hat{\Pr}[\bar{\delta}^{*} \le 0],\; \hat{\Pr}[\bar{\delta}^{*} \ge 0]\bigr)\Bigr)
```

The 95% confidence interval is the 2.5th to 97.5th percentile of the resampled means. Pairing removes query difficulty, which dominates variance in IR: an easy query is easy for every system. We run 30 planned tests (6 comparisons × 5 metrics) at α = 0.05 without multiplicity correction and flag this in Section 7.

## 4 Experimental setup

All six systems are evaluated on the same 323 NFCorpus test queries with no parameter tuned on test data.

**Data.** We use the BEIR release of NFCorpus (Hugging Face BeIR/nfcorpus and BeIR/nfcorpus-qrels). Queries are short — median 2 words, mean 3.3 — while documents average 12.8 title words and 221 abstract words. Relevance is dense: a test query has on average 38.2 judged-relevant documents (median 16, maximum 475), which explains why Recall@100 stays low for every system.

| Property | Train | Dev | Test |
| --- | ---: | ---: | ---: |
| Queries with judgments | 2,590 | 324 | 323 |
| Relevant documents per query, mean (median) | 42.7 (18) | 35.1 (18.5) | 38.2 (16) |
| Judgments graded 1 / graded 2 | 110,575 / 0 | 10,864 / 521 | 11,758 / 576 |
| Role in this study | not used | reserved for tuning | final evaluation only |

An audit script checked the data before any experiment: 0 duplicate document or query IDs, 0 empty documents or queries, 0 judgments pointing to missing documents and 0 overlap between splits.

**Protocol.** Every system retrieves a top-100 list per query (the reranker returns its top P). Runs are stored as TREC run files and JSON, each with a manifest recording configuration, code version, timing and device. Metrics are computed with pytrec_eval over all 323 queries.

**Hardware and timing.** Experiments ran on an Apple M1 Pro (32 GB) with PyTorch’s MPS backend; the course demonstration runs on the same code on a Colab GPU or locally. Latency is the mean wall-clock time per query for retrieval of the top 100: lexical scoring on CPU; query encoding plus exact FAISS search for dense models, excluding the one-time corpus encoding; and BM25 + MedCPT + fusion end to end for the hybrid. Reranking latency is reported separately and summed for the full pipeline.

**Reproducibility.** One command (scripts/reproduce.py) re-runs audit → six systems → evaluation → statistics → figures, skipping steps whose artifacts exist. The code base has 248 passing unit tests, including hand-computed BM25 and RRF examples and a cross-check of every metric against pytrec_eval.

## 5 Results

Moving from lexical to dense retrieval raises nDCG@10 by about 0.07; every later stage moves it by about 0.01. Table 1 gives the primary metrics; Figures 4–7 show recall depth, significance, the reranking pool and the cost of each gain.

**Table 1.** Primary metrics, NFCorpus test, n = 323. Bold = best in column.

| System | P@1 | P@10 | R@100 | MAP | MRR@10 | nDCG@10 | ms / query |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TF-IDF | 0.427 | 0.217 | 0.237 | 0.137 | 0.506 | 0.305 | 3.6 |
| BM25 | 0.421 | 0.207 | 0.230 | 0.133 | 0.494 | 0.295 | 2.2 |
| BGE (general dense) | 0.455 | **0.280** | 0.337 | **0.183** | 0.556 | 0.371 | 2.7 |
| MedCPT (biomedical dense) | 0.468 | 0.270 | **0.349** | 0.182 | 0.549 | 0.365 | **1.9** |
| Hybrid BM25 + MedCPT (RRF) | 0.480 | 0.260 | 0.339 | 0.181 | **0.568** | 0.362 | 4.1 |
| Hybrid + cross-encoder (P = 50) | **0.483** | 0.277 | 0.278† | 0.176† | 0.567 | **0.373** | 1,949.7 |

† Limited by the 50-document candidate pool; not comparable with top-100 runs. Reranked latency = 4.1 ms hybrid + 1,945.6 ms reranking.

**RQ1 — BM25 vs TF-IDF.** TF-IDF is higher on every metric and significantly so on P@10 (+0.010, p = 0.017), Recall@100 (+0.008, p = 0.010) and nDCG@10 (+0.010, p = 0.030). H1 is rejected as measured; Section 6.3 shows that part of this gap is an artifact of how the two baselines fill their lists.

**RQ2 — dense vs lexical.** Both dense models beat BM25 on all five primary metrics with p < 0.005. Against BM25, MedCPT adds 0.070 nDCG@10 (95% CI 0.048–0.093) and 0.119 Recall@100 (0.097–0.142). This is the study’s most robust result.

**RQ3 — biomedical vs general dense.** No BGE–MedCPT difference is significant (all p ≥ 0.12). BGE leads on P@10, MAP, MRR@10 and nDCG@10; MedCPT leads on Recall@100 and P@1. H2 is not supported.

**RQ4 — hybrid vs components.** The hybrid has the best P@1 (0.480) and MRR@10 (0.568) of the first-stage systems, but MedCPT alone has significantly higher Recall@100 (+0.010, p = 0.040), and the hybrid is not significantly better than MedCPT on any metric. H3 is not supported against MedCPT; BM25 vs hybrid was not among the planned tests.

**RQ5 — reranking.** Reranking the hybrid’s top 50 raises P@10 significantly (+0.017, p = 0.015) and gives the highest nDCG@10 in the study, but the nDCG@10 gain (+0.011, 95% CI −0.006 to +0.028) is not significant (p = 0.194). H4 is partly supported. The pool ablation (Figure 6) is non-monotonic: nDCG@10 is 0.364, 0.373 and 0.366 at P = 20, 50 and 100, while MAP rises with P (0.159, 0.176, 0.185) because a larger pool keeps more relevant documents in the list.

**RQ6 — efficiency.** First-stage retrieval costs 2–4 ms per query for every system; dense retrieval is no slower than BM25 once the corpus is encoded. Reranking 50 candidates costs 1,946 ms, about 480 times the hybrid, for a gain that is not significant on nDCG@10 (Figure 7). Reranking latency grows linearly with the pool: 765, 1,942 and 3,918 ms for P = 20, 50 and 100, i.e. about 39 ms per candidate on this hardware.

<!-- figure:recall -->

**Figure 4.** The dense systems separate from the lexical ones as depth grows; the reranked list stops gaining at 50 because it holds only 50 documents.

<!-- figure:forest -->

**Figure 5.** Every confidence interval for dense minus BM25 lies far from zero; every later step’s interval straddles or hugs zero.

<!-- figure:pool -->

**Figure 6.** Effectiveness at the top of the list peaks at a pool of 50, while MAP needs the larger pool to recover documents a short list drops.

<!-- figure:cost -->

**Figure 7.** All first-stage systems cost 2–4 ms per query; on the frontier, only the cross-encoder buys more nDCG@10, and it buys very little.

## 6 Analysis

The stored runs explain the headline numbers: lexical and dense retrievers find largely different documents, their scores cannot be added, and the lexical baselines differ in how they fill short lists. Every figure in this section is computed from the 323 test-query runs in results/runs.

### 6.1 Score scales are incommensurable

The top-ranked BM25 score has a median of 10.6 (5th–95th percentile 1.1–22.9) and BM25 scores range from −30.1 to 37.9; the top MedCPT dot product has a median of 65.3 (59.9–71.7) and all MedCPT scores lie between 47.4 and 76.3; BGE cosines lie between 0.37 and 0.87. MedCPT scores barely vary within or across queries while BM25 scores vary twenty-fold, so a raw sum would be decided almost entirely by BM25 for some queries and by MedCPT for others. This is the reason for rank fusion (Figure 8).

<!-- figure:scores -->

**Figure 8.** On a shared axis the two score distributions do not overlap; their per-query correlation is only 0.26.

### 6.2 The two retrievers find different documents

BM25 and MedCPT share on average 2.8 of their top 10 documents (median 2) and 21.4 of their top 100; their top-100 union averages 145.9 documents. The two dense models agree more (4.1 of 10) and the two lexical models most (5.8 of 10). Low overlap is what makes fusion attractive, but it cuts both ways: RRF rewards documents that appear in both lists, and when only one list is right, RRF gives the wrong list’s top documents the same weight. The fused top 10 keeps 6.4 of MedCPT’s top 10 and 4.8 of BM25’s, so roughly a third of MedCPT’s first page is replaced by BM25 candidates — which helps when BM25 is right (P@1 and MRR rise) and hurts recall when it is wrong (Figure 9).

<!-- figure:overlap -->

**Figure 9.** 56 queries share no document between the two first pages; only one query shares all ten.

RRF also produces ties: 55 queries (17%) have at least one exact score tie inside the top 10, because a document at rank r in one list scores 1/(60 + r) whether it came from BM25 or MedCPT. Ties are broken by document ID, an arbitrary order.

### 6.3 Why TF-IDF beat BM25

Two implementation facts, both visible in the runs, qualify the rejection of H1.

1. **Unequal list depth.** BM25 returns only documents that share a query term: 25 queries get an empty list, 79 get fewer than 10 documents and 127 fewer than 100. TF-IDF always returns 100 documents, padding with cosine-0 documents in an arbitrary order: 614 of its top-10 slots (in exactly those 79 queries) and 10,564 of its top-100 slots hold zero-similarity documents. With 38.2 relevant documents per query, a random document is relevant with probability of about 1.05%, so padding alone would be expected to add about 6 relevant documents to TF-IDF’s top 10s and about 111 to its top 100s across the test set — free credit that BM25 cannot earn.
2. **Negative idf.** Without stopword removal, the BM25 idf in Section 3.3 is negative for terms in more than half of the corpus. 69 queries contain such a term, 5,767 retrieved BM25 entries have negative scores and 322 of them sit in a top 10. A document is penalized for containing “the”, which TF-IDF’s floor of idf ≥ 1 never does.

Neither effect is a bug in the metric; both are ordinary toolkit defaults. A controlled re-test — truncating zero-score TF-IDF documents, flooring BM25 idf at 0 and tuning k1 and b on the dev split — is the cleanest way to settle RQ1 and is left for future work.

### 6.4 Where each method fails

Using rank ≤ 10 as success and rank > 50 or absent as failure, over all 12,334 judged test pairs: MedCPT succeeds where BM25 fails 244 times and the reverse happens 52 times; the hybrid rescues 76 BM25 failures but only 17 MedCPT failures; and the reranker moves 926 relevant documents up and 832 down within its pool. Table 2 follows one judged-relevant document for each of five diverse queries.

**Table 2.** Rank of one judged-relevant document per query (– = not in top 100).

| Query (test ID) | Relevant document (grade) | TF-IDF | BM25 | BGE | MedCPT | Hybrid | + CE |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| salmon (PLAIN-2040) | Methylmercury toxicity in Atlantic salmon (1) | 3 | 2 | 2 | – | 8 | 6 |
| Exploiting Autophagy to Live Longer (PLAIN-12) | Why human lifespan is rapidly increasing (1) | – | – | 5 | 1 | 10 | 3 |
| canker sores (PLAIN-817) | Humoral immunity … recurrent aphthous ulcers (1) | – | – | 14 | 1 | 1 | 21 |
| Fosamax (PLAIN-1214) | Bisphosphonate-associated osteonecrosis of the jaw (1) | – | – | – | 1 | 1 | 12 |
| What’s Driving America’s Obesity Problem? (PLAIN-33) | Physical activity energy expenditure has not declined (2) | 2 | 4 | 86 | – | 35 | 20 |

The rows show three distinct failure modes. **Vocabulary mismatch** (autophagy, canker sores, Fosamax): lexical models miss entirely and MedCPT ranks the paper first. **Semantic drift** (salmon, obesity): exact words find the paper and MedCPT does not — for “salmon”, MedCPT’s list wanders to fishmeal supply, raw fish fillets and oysters. **Fusion and reranking dilution**: fusion moves the salmon paper from 2 to 8 and the obesity paper from BM25’s 4 to 35, and the cross-encoder pushes the canker-sores paper from 1 to 21, plausibly because the abstract never uses the query’s lay term.

### 6.5 How much the cross-encoder reorders

The cross-encoder changes the order substantially: the Kendall τ between the hybrid’s top-50 order and the reranked order averages 0.34, and only 5.4 of the hybrid’s top 10 remain in the reranked top 10. Large reordering with a small, non-significant net nDCG@10 gain is consistent with the near-even 926 / 832 split above: the cross-encoder is confident but not reliably right on lay queries, which differ from the PubMed search-log queries it was trained on.

## 7 Discussion

For lay biomedical queries, the representation matters more than the pipeline built around it: switching to a dense encoder is worth seven times more nDCG@10 than fusion and reranking combined, at no latency cost once the corpus is encoded.

**What the hypotheses taught us.** H1 failed for reasons rooted in defaults rather than in the BM25 model (Section 6.3). H2 failed because a strong general encoder already bridges the lay–technical gap on NFCorpus; MedCPT’s training queries come from PubMed users, who write more like authors than NutritionFacts readers do. H3 failed because RRF is symmetric while the two retrievers are not equally reliable: MedCPT is right far more often (244 vs 52), yet RRF weights BM25 equally. H4 held for P@10 and latency but not, significantly, for nDCG@10.

**Design implications.**

- **Weight the fusion.** A weighted RRF, w × 1/(k + rank<sub>MedCPT</sub>) + (1 − w) × 1/(k + rank<sub>BM25</sub>), or a convex combination of normalized scores (Bruch et al., 2023), tuned on the 324 dev queries, would let the stronger retriever dominate. A query-dependent weight — trusting BM25 only when its top score is high, since a low or negative top score signals vocabulary mismatch — targets exactly the failures in Table 2.
- **Spend reranking budget on depth, not on every query.** At about 39 ms per candidate on this hardware, the cross-encoder is affordable for interactive use only on a GPU or with a smaller pool. The non-monotonic pool curve suggests P ≈ 50 is a reasonable default.
- **Fix mismatch at the text level.** Learned sparse models such as SPLADE (Formal et al., 2021) expand both queries and documents with related terms and would let a lexical index match “canker sores” to “aphthous”. LLM-based expansion (HyDE, query2doc) generates a hypothetical answer in the documents’ vocabulary before retrieval; this targets our vocabulary-mismatch class directly but adds generation latency and a risk of hallucinated medical content.
- **Reconsider the reranker.** Listwise LLM rerankers (Sun et al., 2023; Pradeep et al., 2023) reason over all candidates at once and may handle lay phrasing better than a cross-encoder trained on PubMed logs, at higher cost. Domain adaptation of the cross-encoder on NFCorpus training queries (e.g. generative pseudo-labelling) is a cheaper alternative.
- **Retrieval-augmented generation.** In a RAG health assistant, first-stage recall bounds answer quality. Our results argue for a dense first stage with recall-oriented fusion and a light reranker, and for evaluating retrieval separately before judging generated answers.

### 7.1 Limitations and threats to validity

- **One collection, 323 queries.** Effects below about 0.01 nDCG@10 are hard to detect at this sample size; a planned extension to SciFact and TREC-COVID with dev-only tuning is implemented in the repository but has not been run.
- **Multiple comparisons.** The 30 tests are uncorrected. Applying Holm–Bonferroni to the reported p-values, only the nine tests with p < 0.0001 survive: dense vs BM25 on P@10, Recall@100, MAP and nDCG@10 (both dense models), and the pool-capped reranker Recall@100. Dense vs BM25 on MRR@10 (p = 0.003–0.005) and every finding with p between 0.01 and 0.05 — TF-IDF vs BM25, MedCPT vs hybrid recall, reranker P@10 — should be read as suggestive.
- **Untuned baselines.** BM25 (k1, b) and RRF (k) use literature defaults, and no system was tuned on the dev split; tuned baselines may close some gaps.
- **Incomplete judgments.** Unjudged documents count as non-relevant. Dense models retrieve documents that lexical pooling may never have surfaced, which can understate dense effectiveness.
- **List-depth asymmetry.** TF-IDF pads to 100 documents while BM25 does not (Section 6.3); the reranker returns 50. Depth-dependent metrics (Recall@100, MAP) are not like-for-like across these rows.
- **Hardware.** Latency was measured on an Apple M1 Pro with MPS; absolute numbers will differ on a GPU, though the ordering of costs will not.
- **Ties.** RRF ties (55 queries) are broken by document ID, and trec_eval breaks score ties by its own rule; small metric differences between evaluators can arise from this alone.

## 8 Conclusion

On NFCorpus, dense retrieval is the one change that clearly pays: it significantly beats BM25 on every primary metric and costs nothing extra per query once the corpus is encoded. Equal-weight rank fusion improves how early the first relevant document appears but does not beat MedCPT alone, and cross-encoder reranking gives the best nDCG@10 and a significant P@10 gain at roughly 480 times the latency. Run-level analysis explains why: the retrievers overlap on fewer than three of their top 10 documents, RRF weights a weaker retriever equally, and the lexical baselines differ in list depth and idf floor in ways that favour TF-IDF. The most promising next steps are dev-tuned weighted fusion, term-expansion methods that target vocabulary mismatch directly, and validation on further biomedical collections.

**Code and data.** Code, runs, manifests, figures and a live demonstration (BM25, MedCPT, RRF and cross-encoder on arbitrary queries, with live scoring of judged queries) are at [github.com/Arungharami/biomedical-hybrid-ir](https://github.com/Arungharami/biomedical-hybrid-ir).

**AI-use disclosure.** [Edit so that it is exactly true.] AI assistants (Claude) were used as a coding aid — code suggestions, debugging, the demonstration app and evaluation scripts — and to help draft and edit this paper. The author designed the study, ran the experiments, verified every reported number against the stored result files, and is responsible for the analysis and conclusions.

## References

- Boteva, V., Gholipour, D., Sokolov, A., and Riezler, S. (2016). A full-text learning to rank dataset for medical information retrieval. ECIR 2016.
- Bruch, S., Gai, S., and Ingber, A. (2023). An analysis of fusion functions for hybrid retrieval. ACM Transactions on Information Systems, 42(1).
- Cormack, G. V., Clarke, C. L. A., and Büttcher, S. (2009). Reciprocal rank fusion outperforms Condorcet and individual rank learning methods. SIGIR 2009.
- Formal, T., Piwowarski, B., and Clinchant, S. (2021). SPLADE: Sparse lexical and expansion model for first stage ranking. SIGIR 2021.
- Gao, L., Ma, X., Lin, J., and Callan, J. (2023). Precise zero-shot dense retrieval without relevance labels (HyDE). ACL 2023.
- Gu, Y., Tinn, R., Cheng, H., et al. (2021). Domain-specific language model pretraining for biomedical natural language processing. ACM Transactions on Computing for Healthcare, 3(1).
- Izacard, G., Caron, M., Hosseini, L., et al. (2022). Unsupervised dense information retrieval with contrastive learning. Transactions on Machine Learning Research.
- Järvelin, K., and Kekäläinen, J. (2002). Cumulated gain-based evaluation of IR techniques. ACM Transactions on Information Systems, 20(4).
- Jin, Q., Kim, W., Chen, Q., et al. (2023). MedCPT: Contrastive pre-trained transformers with large-scale PubMed search logs for zero-shot biomedical information retrieval. Bioinformatics, 39(11).
- Johnson, J., Douze, M., and Jégou, H. (2019). Billion-scale similarity search with GPUs. IEEE Transactions on Big Data, 7(3).
- Karpukhin, V., Oğuz, B., Min, S., et al. (2020). Dense passage retrieval for open-domain question answering. EMNLP 2020.
- Khattab, O., and Zaharia, M. (2020). ColBERT: Efficient and effective passage search via contextualized late interaction over BERT. SIGIR 2020.
- Lee, J., Yoon, W., Kim, S., et al. (2020). BioBERT: a pre-trained biomedical language representation model for biomedical text mining. Bioinformatics, 36(4).
- Lewis, P., Perez, E., Piktus, A., et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. NeurIPS 2020.
- Lin, J., Nogueira, R., and Yates, A. (2021). Pretrained Transformers for Text Ranking: BERT and Beyond. Morgan & Claypool.
- Manning, C. D., Raghavan, P., and Schütze, H. (2008). Introduction to Information Retrieval. Cambridge University Press.
- Muennighoff, N., Tazi, N., Magne, L., and Reimers, N. (2023). MTEB: Massive text embedding benchmark. EACL 2023.
- Nogueira, R., and Cho, K. (2019). Passage re-ranking with BERT. arXiv:1901.04085.
- Nogueira, R., Yang, W., Lin, J., and Cho, K. (2019). Document expansion by query prediction. arXiv:1904.08375.
- Pradeep, R., Sharifymoghaddam, S., and Lin, J. (2023). RankZephyr: Effective and robust zero-shot listwise reranking is a breeze! arXiv:2312.02724.
- Robertson, S., and Zaragoza, H. (2009). The probabilistic relevance framework: BM25 and beyond. Foundations and Trends in Information Retrieval, 3(4).
- Salton, G., Wong, A., and Yang, C. S. (1975). A vector space model for automatic indexing. Communications of the ACM, 18(11).
- Smucker, M. D., Allan, J., and Carterette, B. (2007). A comparison of statistical significance tests for information retrieval evaluation. CIKM 2007.
- Sun, W., Yan, L., Ma, X., et al. (2023). Is ChatGPT good at search? Investigating large language models as re-ranking agents. EMNLP 2023.
- Thakur, N., Reimers, N., Rücklé, A., Srivastava, A., and Gurevych, I. (2021). BEIR: A heterogeneous benchmark for zero-shot evaluation of information retrieval models. NeurIPS 2021 Datasets and Benchmarks.
- Wang, L., Yang, N., and Wei, F. (2023). Query2doc: Query expansion with large language models. EMNLP 2023.
- Xiao, S., Liu, Z., Zhang, P., and Muennighoff, N. (2023). C-Pack: Packaged resources to advance general Chinese embedding. arXiv:2309.07597.
