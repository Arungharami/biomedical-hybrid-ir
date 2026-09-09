# Reproducibility

## One-command reproduction

```bash
python scripts/reproduce.py --config configs/default.yaml
```

Runs, in order: dataset audit → TF-IDF → BM25 → BGE → MedCPT → hybrid RRF →
cross-encoder reranking → evaluation → statistical analysis → figures → web
export. Each step checks for its expected output artifact under `results/`
and skips recomputation if it's already present (expensive embedding steps
in particular are never silently recomputed) — see the script's `--force`
flag to override. ⚪ Script scaffolding pending (M2+).

## Environment

- Python 3.11 (PyTorch/FAISS wheels lag behind newer CPython releases;
  verified empirically that 3.14, the system default on the dev machine used
  for this project, has no compatible wheels as of 2026-09-09)
- Key library versions are recorded per-run in `results/manifests/*.json`
  (see `src/biomedical_ir/manifests.py`), not hand-maintained here, so they
  can never drift out of sync with what actually ran.
- `seed = 42` throughout.

## Device handling

`src/biomedical_ir/utils.py::detect_device()` prefers CUDA (Colab / most
cloud GPUs), then Apple MPS (used for local development on this project's
M1 Pro machine), then falls back to CPU. Configurable via
`configs/default.yaml -> device.preference` or the `BIOMEDICAL_IR_DEVICE`
env var.

## Colab notebooks

| Notebook | Purpose | Status |
|---|---|---|
| `00_environment_setup.ipynb` | Install deps, verify GPU | ⚪ Pending |
| `01_nfcorpus_dataset_audit.ipynb` | Download + validate NFCorpus | ⚪ Pending |
| `02_tfidf_baseline.ipynb` | M1 | ⚪ Pending |
| `03_bm25_baseline.ipynb` | M2 | ⚪ Pending |
| `04_bge_dense_retrieval.ipynb` | M3 | ⚪ Pending |
| `05_medcpt_dense_retrieval.ipynb` | M4 | ⚪ Pending |
| `06_hybrid_rrf.ipynb` | M5 | ⚪ Pending |
| `07_cross_encoder_reranking.ipynb` | M6 | ⚪ Pending |
| `08_evaluation.ipynb` | Metrics | ⚪ Pending |
| `09_statistical_analysis.ipynb` | Significance testing | ⚪ Pending |
| `10_error_analysis.ipynb` | Query-level diagnostics | ⚪ Pending |
| `11_export_research_results.ipynb` | Export web/data JSON | ⚪ Pending |
| `Biomedical_Hybrid_IR_Full_Pipeline.ipynb` | Master run-all notebook | ⚪ Pending |

All notebooks import reusable logic from `src/biomedical_ir/` rather than
duplicating code (Section 21 of the project spec).

## Known limitations (living list)

- This is a from-scratch build started 2026-09-09; as of M0/M1 only dataset
  ingestion and validation are real. See the README's Experiment status
  table for the authoritative current state.
