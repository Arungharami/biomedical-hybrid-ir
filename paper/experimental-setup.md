# 6. Experimental Setup & 7. Evaluation Metrics

## 6. Experimental Setup

**Dataset:** BeIR/nfcorpus + BeIR/nfcorpus-qrels (3,633 documents, 3,237
queries; 2,590/324/323 train/dev/test queries with qrels). Verified against
the live Hugging Face Hub, not assumed from documentation
(`docs/dataset.md`).

**Hardware:** Apple M1 Pro (32GB RAM), PyTorch MPS backend for all
transformer inference (BGE, MedCPT encoders, MedCPT cross-encoder); pure
CPU for TF-IDF, BM25, and RRF fusion. Recorded per-experiment in
`results/manifests/*.json`, not hand-maintained here (so it can never drift
out of sync with what actually ran).

**Frozen parameters** (no tuning against the test set, Section 4's data
leakage rule):
- BM25: `k1=1.2, b=0.75` (literature defaults, `tuning.enabled: false`)
- RRF: `k=60`, candidate depth 100
- Reranker: candidate pool 50 (default; 20/50/100 all tested as ablation A6)

**Batching / sequence lengths:** BGE — batch 32, max length 512, query
instruction `"Represent this sentence for searching relevant passages: "`.
MedCPT — batch 32, query max length 64, article max length 512, articles as
`[title, text]` pairs. Cross-encoder — batch 32, max length 512, articles
as `"{title}. {text}"`.

**Seed:** 42 throughout (`biomedical_ir.utils.set_seed`).

**Library versions:** Python 3.11.16, PyTorch 2.14.0, Transformers 5.16.1,
sentence-transformers 6.0.1, datasets 5.0.1, FAISS 1.15.0, scikit-learn
1.9.0, pytrec_eval (latest at time of run) — recorded exactly, per
experiment, in every `results/manifests/*.json`.

## 7. Evaluation Metrics

See [docs/evaluation.md](../docs/evaluation.md) for the finalized metric
definitions and evaluation protocol (identical for all six models, same test
qrels). Metric formulas: Precision/Recall/MAP (Manning et al., 2008), nDCG
(Järvelin & Kekäläinen, 2002).
