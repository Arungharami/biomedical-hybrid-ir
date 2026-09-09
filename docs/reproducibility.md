# Reproducibility

## One-command reproduction

```bash
python scripts/reproduce.py --config configs/default.yaml
```

✅ **Implemented and verified** (`scripts/reproduce.py`). Runs, in order:
dataset audit → TF-IDF → BM25 → BGE → MedCPT → hybrid RRF → cross-encoder
reranking → statistical/efficiency analysis → error analysis → web export
(the last step runs automatically once `scripts/export_web_results.py`
exists, M11). Each step is **skipped** if its expected output artifact
already exists under `results/` (verified: a full run against this
project's real, complete `results/` directory correctly skips all 9 core
steps) — pass `--force` to recompute everything anyway, or `--from <step>`
to resume after fixing a failure partway through.

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

## Colab notebooks (M9 — complete)

| Notebook | Purpose | Status |
|---|---|---|
| `00_environment_setup.ipynb` | Install deps, verify GPU/MPS, print library versions | ✅ Verified (executed for real) |
| `01_nfcorpus_dataset_audit.ipynb` | Download + validate NFCorpus | ✅ Verified (M1) |
| `02_tfidf_baseline.ipynb` | M1 TF-IDF | ✅ Verified (executed for real) |
| `03_bm25_baseline.ipynb` | M2 BM25 | ✅ Verified (executed for real) |
| `04_bge_dense_retrieval.ipynb` | M3 BGE | ✅ Complete (calls the verified `scripts/run_bge.py`; not re-executed in-session — ~2 min runtime) |
| `05_medcpt_dense_retrieval.ipynb` | M4 MedCPT | ✅ Complete (calls the verified `scripts/run_medcpt.py`; not re-executed in-session — ~3 min runtime) |
| `06_hybrid_rrf.ipynb` | M5 Hybrid RRF | ✅ Verified (executed for real) |
| `07_cross_encoder_reranking.ipynb` | M6 Reranking | ✅ Complete (calls the verified `scripts/run_reranker.py`; not re-executed in-session — ~40 min runtime on MPS for all 3 pools) |
| `08_evaluation.ipynb` | Cross-model comparison table | ✅ Verified (executed for real) |
| `09_statistical_analysis.ipynb` | Significance testing | ✅ Verified (executed for real) |
| `10_error_analysis.ipynb` | Query-level diagnostics | ✅ Verified (executed for real) |
| `11_export_research_results.ipynb` | Export web/data JSON (M11) | ✅ Verified (executed for real; correctly reports "pending" until M11's export script exists) |
| `Biomedical_Hybrid_IR_Full_Pipeline.ipynb` | Master run-all notebook | ✅ Complete (calls `scripts/reproduce.py`, itself verified to correctly skip all cached steps) |

All notebooks import reusable logic from `src/biomedical_ir/` rather than
duplicating code (Section 21 of the project spec) — each numbered notebook
is a thin wrapper around the identically-named `scripts/*.py` file, plus
markdown explaining the real results and a couple of inline
teaching/sanity-check cells (e.g. notebook 06 reproduces the RRF
hand-computation from `tests/test_fusion.py` inline). 8 of 13 notebooks
were executed end-to-end in a real Jupyter kernel via `nbclient` as part of
building this project (not just validated as well-formed JSON); the
remaining 5 (BGE, MedCPT, reranker, and the two notebooks that call them)
call scripts already independently verified by direct CLI execution
earlier in this project's history and were not re-executed here solely to
avoid a redundant ~45-minute rerun.

## Known limitations (living list)

- This is a from-scratch build started 2026-09-09; as of M0-M7, all six
  retrieval models plus statistical/efficiency analysis are real
  (`results/runs/`, `results/metrics/`, `results/manifests/`,
  `results/tables/statistical_tests.*`, `results/tables/efficiency.*`).
  `scripts/run_{tfidf,bm25,bge,medcpt,hybrid,reranker}.py` and
  `scripts/evaluate_all.py` are standalone entry points for now; the
  unifying `scripts/reproduce.py` orchestrator is still pending (M8+). See
  the README's Experiment status table for the authoritative current state.
- Dense/cross-encoder embeddings (BGE, MedCPT, reranker) are not currently
  cached to disk between runs -- each script invocation re-encodes/re-scores
  from scratch. Fine at this corpus size (3,633 docs) but should be
  revisited if `scripts/reproduce.py`'s "resume from cache" requirement
  (Section 24) is to be honored precisely at a larger scale.
- **Cross-encoder reranking (M6) is slow on this project's hardware:**
  ~765-3918 ms/query depending on candidate pool size (20/50/100), measured
  on Apple M1 Pro (MPS). This is NOT representative of GPU-optimized
  production latency -- PyTorch's MPS backend lacks some of the fused
  attention kernels CUDA has for transformer inference. Reported as an
  honest, real measurement on the hardware actually used, not smoothed or
  extrapolated to a hypothetical GPU number.
- **The reranker's Recall@100/MAP are capped by its candidate pool size**
  (a cross-encoder can only reorder candidates it's given) -- this is a
  genuine methodological property, not a bug, but means the M6 row in
  `results/tables/main_results.md` is not directly apples-to-apples with
  the other rows' true top-100 rankings on those two metrics specifically.
  See that table's M6 observation section for the full mechanism and the
  pool-size ablation (A6) that confirms it exactly.
