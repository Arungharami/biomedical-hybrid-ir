# Effectiveness / efficiency summary

| Model | Device | Embedding dim | Index size (KB) | Latency (ms/query) | nDCG@10 | MAP | Recall@100 |
|---|---|---:|---:|---:|---:|---:|---:|
| TF-IDF | cpu | - | - | 3.631 | 0.3050 | 0.1372 | 0.2372 |
| BM25 | cpu | - | - | 2.155 | 0.2954 | 0.1333 | 0.2295 |
| BGE | mps | 768 | 10899.0 | 2.678 | 0.3712 | 0.1831 | 0.3368 |
| MedCPT | mps | 768 | 10899.0 | 1.871 | 0.3654 | 0.1824 | 0.3488 |
| Hybrid RRF | cpu | - | - | 4.069 | 0.3620 | 0.1809 | 0.3389 |
| Hybrid+Reranker | mps | - | - | 1945.644 | 0.3731 | 0.1760 | 0.2782 |
