# Statistical significance tests (paired bootstrap, n_resamples=10000, seed=42)

> Comparisons named in Section 16 of the project spec. Query-level paired bootstrap over the primary metrics; p < 0.05 flagged SIGNIFICANT. No comparison here should be read as proving a hypothesis outside the metric/comparison it specifically tests.

| Comparison | Metric | A mean | B mean | Diff (A-B) | 95% CI | p-value | Significant | n |
|---|---|---:|---:|---:|---|---:|:---:|---:|
| TF-IDF vs BM25 | P@10 | 0.2167 | 0.2071 | +0.0096 | [+0.0019, +0.0183] | 0.0170 | **yes** | 323 |
| TF-IDF vs BM25 | Recall@100 | 0.2372 | 0.2295 | +0.0077 | [+0.0014, +0.0160] | 0.0100 | **yes** | 323 |
| TF-IDF vs BM25 | MAP | 0.1372 | 0.1333 | +0.0038 | [-0.0007, +0.0085] | 0.0954 | no | 323 |
| TF-IDF vs BM25 | MRR@10 | 0.5062 | 0.4939 | +0.0123 | [-0.0107, +0.0354] | 0.2946 | no | 323 |
| TF-IDF vs BM25 | nDCG@10 | 0.3050 | 0.2954 | +0.0096 | [+0.0010, +0.0183] | 0.0296 | **yes** | 323 |
| BM25 vs BGE | P@10 | 0.2071 | 0.2796 | -0.0724 | [-0.0920, -0.0536] | 0.0000 | **yes** | 323 |
| BM25 vs BGE | Recall@100 | 0.2295 | 0.3368 | -0.1073 | [-0.1285, -0.0861] | 0.0000 | **yes** | 323 |
| BM25 vs BGE | MAP | 0.1333 | 0.1831 | -0.0498 | [-0.0645, -0.0364] | 0.0000 | **yes** | 323 |
| BM25 vs BGE | MRR@10 | 0.4939 | 0.5556 | -0.0618 | [-0.1015, -0.0236] | 0.0030 | **yes** | 323 |
| BM25 vs BGE | nDCG@10 | 0.2954 | 0.3712 | -0.0757 | [-0.0988, -0.0536] | 0.0000 | **yes** | 323 |
| BM25 vs MedCPT | P@10 | 0.2071 | 0.2697 | -0.0625 | [-0.0817, -0.0443] | 0.0000 | **yes** | 323 |
| BM25 vs MedCPT | Recall@100 | 0.2295 | 0.3488 | -0.1193 | [-0.1421, -0.0969] | 0.0000 | **yes** | 323 |
| BM25 vs MedCPT | MAP | 0.1333 | 0.1824 | -0.0491 | [-0.0641, -0.0354] | 0.0000 | **yes** | 323 |
| BM25 vs MedCPT | MRR@10 | 0.4939 | 0.5487 | -0.0549 | [-0.0940, -0.0162] | 0.0046 | **yes** | 323 |
| BM25 vs MedCPT | nDCG@10 | 0.2954 | 0.3654 | -0.0700 | [-0.0931, -0.0480] | 0.0000 | **yes** | 323 |
| BGE vs MedCPT | P@10 | 0.2796 | 0.2697 | +0.0099 | [-0.0034, +0.0235] | 0.1512 | no | 323 |
| BGE vs MedCPT | Recall@100 | 0.3368 | 0.3488 | -0.0120 | [-0.0279, +0.0028] | 0.1238 | no | 323 |
| BGE vs MedCPT | MAP | 0.1831 | 0.1824 | +0.0007 | [-0.0134, +0.0139] | 0.9130 | no | 323 |
| BGE vs MedCPT | MRR@10 | 0.5556 | 0.5487 | +0.0069 | [-0.0260, +0.0387] | 0.6824 | no | 323 |
| BGE vs MedCPT | nDCG@10 | 0.3712 | 0.3654 | +0.0057 | [-0.0133, +0.0241] | 0.5408 | no | 323 |
| MedCPT vs Hybrid RRF | P@10 | 0.2697 | 0.2598 | +0.0099 | [-0.0028, +0.0229] | 0.1262 | no | 323 |
| MedCPT vs Hybrid RRF | Recall@100 | 0.3488 | 0.3389 | +0.0099 | [+0.0004, +0.0199] | 0.0396 | **yes** | 323 |
| MedCPT vs Hybrid RRF | MAP | 0.1824 | 0.1809 | +0.0015 | [-0.0054, +0.0085] | 0.6622 | no | 323 |
| MedCPT vs Hybrid RRF | MRR@10 | 0.5487 | 0.5678 | -0.0191 | [-0.0498, +0.0116] | 0.2288 | no | 323 |
| MedCPT vs Hybrid RRF | nDCG@10 | 0.3654 | 0.3620 | +0.0034 | [-0.0106, +0.0178] | 0.6270 | no | 323 |
| Hybrid RRF vs Hybrid+Reranker | P@10 | 0.2598 | 0.2765 | -0.0167 | [-0.0300, -0.0034] | 0.0150 | **yes** | 323 |
| Hybrid RRF vs Hybrid+Reranker | Recall@100 | 0.3389 | 0.2782 | +0.0607 | [+0.0496, +0.0735] | 0.0000 | **yes** | 323 |
| Hybrid RRF vs Hybrid+Reranker | MAP | 0.1809 | 0.1760 | +0.0049 | [-0.0036, +0.0148] | 0.2912 | no | 323 |
| Hybrid RRF vs Hybrid+Reranker | MRR@10 | 0.5678 | 0.5670 | +0.0009 | [-0.0298, +0.0325] | 0.9624 | no | 323 |
| Hybrid RRF vs Hybrid+Reranker | nDCG@10 | 0.3620 | 0.3731 | -0.0111 | [-0.0275, +0.0061] | 0.1944 | no | 323 |
