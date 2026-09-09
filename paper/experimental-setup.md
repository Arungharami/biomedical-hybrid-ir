# 6. Experimental Setup & 7. Evaluation Metrics

## 6. Experimental Setup

⚪ **Pending** — will report, once real runs exist: hardware/device used per
model (from `results/manifests/*.json`), library versions, batch sizes, max
sequence lengths, candidate depths, and the frozen final BM25/RRF parameters
(Section 4 data-leakage rule: any tuning happened on `dev` only).

## 7. Evaluation Metrics

See [docs/evaluation.md](../docs/evaluation.md) for the finalized metric
definitions and evaluation protocol (identical for all six models, same test
qrels). Metric formulas: Precision/Recall/MAP (Manning et al., 2008), nDCG
(Järvelin & Kekäläinen, 2002).
