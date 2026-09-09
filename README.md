# Hybrid Biomedical Information Retrieval with Lexical, Dense, and Cross-Encoder Reranking

**A Reproducible Study on NFCorpus**

Course project for **CAP 6776 — Information Retrieval**. Domain: healthcare /
biomedical information retrieval.

> **Status legend:** ✅ Complete · 🟡 In progress · ⚪ Pending · ❌ Failed
> An experiment is only marked ✅ once its output artifact exists under
> `results/` and passes validation — see [Experiment status](#experiment-status).

## Research objective

Build and evaluate a modern biomedical IR system that compares classical
lexical retrieval, general-purpose dense retrieval, biomedical-domain dense
retrieval, hybrid lexical+semantic fusion, and cross-encoder reranking on the
same dataset, qrels, and evaluation protocol — telling one coherent research
story from TF-IDF to a biomedical cross-encoder, with every number backed by
a real, reproducible experiment.

```
TF-IDF → BM25 → General Dense (BGE) → Biomedical Dense (MedCPT)
       → Hybrid (BM25 + MedCPT, RRF) → + MedCPT Cross-Encoder Reranking
```

See [docs/architecture.md](docs/architecture.md) for the full pipeline
diagram and design rationale.

## Dataset

[BeIR/nfcorpus](https://huggingface.co/datasets/BeIR/nfcorpus) +
[BeIR/nfcorpus-qrels](https://huggingface.co/datasets/BeIR/nfcorpus-qrels) —
verified directly against the live Hugging Face Hub (not assumed from
documentation). See [docs/dataset.md](docs/dataset.md) for full provenance,
schema, and the two non-obvious facts about this dataset (the qrels split is
literally named `validation` not `dev`, and relevance labels are graded
0/1/2, not binary).

| | Corpus | Queries (total) | train qrels | dev (`validation`) qrels | test qrels |
|---|---:|---:|---:|---:|---:|
| **Count** | 3,633 docs | 3,237 | 2,590 queries | 324 queries | 323 queries |

Validation (`scripts/audit_dataset.py` → `data/processed/dataset_stats.json`):
**0** duplicate IDs, **0** missing qrel references, **0** empty
queries/documents, **0** train/dev/test split overlap.

## Models

| # | Model | Role | Status |
|---|---|---|---|
| M1 | TF-IDF + cosine similarity | Classical lexical baseline | ⚪ Pending |
| M2 | BM25 (`k1=1.2, b=0.75`) | Classical lexical baseline | ⚪ Pending |
| M3 | [BAAI/bge-base-en-v1.5](https://huggingface.co/BAAI/bge-base-en-v1.5) | General dense retrieval | ⚪ Pending |
| M4 | [ncbi/MedCPT-Query-Encoder](https://huggingface.co/ncbi/MedCPT-Query-Encoder) + [ncbi/MedCPT-Article-Encoder](https://huggingface.co/ncbi/MedCPT-Article-Encoder) | Biomedical dense retrieval | ⚪ Pending |
| M5 | BM25 + MedCPT, Reciprocal Rank Fusion (k=60) | Hybrid retrieval | ⚪ Pending |
| M6 | [ncbi/MedCPT-Cross-Encoder](https://huggingface.co/ncbi/MedCPT-Cross-Encoder) reranking M5's candidates | Biomedical reranking | ⚪ Pending |

Model choices and exact pooling/normalization/input-format decisions are
documented per-model in [docs/models.md](docs/models.md), each verified
against the model's official Hugging Face card rather than assumed.

## Evaluation metrics

Precision@{1,5,10}, Recall@{10,20,50,100}, MRR, MRR@10, MAP, MAP@100,
nDCG@{5,10,20} — computed with `pytrec_eval` (TREC-compatible) and
cross-checked against custom educational implementations
(`src/biomedical_ir/evaluation.py`, `tests/test_metrics.py`). Primary paper
table emphasizes P@10, Recall@100, MAP, MRR@10, nDCG@10, and latency.

## Repository structure

```
biomedical-hybrid-ir/
├── src/biomedical_ir/     # reusable library: data, validation, models, fusion, eval, stats
├── scripts/                # thin CLI entry points calling into biomedical_ir/
├── configs/                # YAML configs (one per model + defaults)
├── tests/                  # pytest unit tests
├── notebooks/               # Colab-compatible notebooks, import from src/
├── data/                    # raw/cache (gitignored) + processed/ (tracked stats)
├── results/                 # runs/ metrics/ manifests/ tables/ figures/ error-analysis/
├── paper/                   # paper-ready markdown sections + references.bib
├── docs/                    # architecture, dataset, models, evaluation, reproducibility
└── web/                     # Next.js research portal (Vercel)
```

## Quick start

```bash
git clone https://github.com/Arungharami/biomedical-hybrid-ir
cd biomedical-hybrid-ir
python3.11 -m venv .venv && source .venv/bin/activate   # PyTorch/FAISS need <=3.13
pip install -r requirements.txt
pip install -e .

pytest -q                        # 28 tests, all passing as of M0/M1
python scripts/audit_dataset.py  # downloads NFCorpus, validates, writes stats
```

## Colab

Run the full pipeline from `notebooks/Biomedical_Hybrid_IR_Full_Pipeline.ipynb`
(Runtime → Run All) once notebooks land in M9. Individual stage notebooks are
listed in [docs/reproducibility.md](docs/reproducibility.md).

## Experiment status

| Milestone | Description | Status |
|---|---|---|
| M0 | Repository foundation, packaging, configs, CI skeleton | ✅ Complete |
| M1 | Dataset ingestion + validation (real NFCorpus, verified against live Hub) | ✅ Complete |
| M2 | TF-IDF + BM25 baselines | ⚪ Pending |
| M3 | BGE general dense retrieval | ⚪ Pending |
| M4 | MedCPT biomedical dense retrieval | ⚪ Pending |
| M5 | Hybrid RRF | ⚪ Pending |
| M6 | MedCPT cross-encoder reranking | ⚪ Pending |
| M7 | Full evaluation, tables, statistical tests, efficiency analysis | ⚪ Pending |
| M8 | Error analysis | ⚪ Pending |
| M9 | Colab notebooks | ⚪ Pending |
| M10 | Paper artifacts (figures, BibTeX) | ⚪ Pending |
| M11 | Next.js research portal | ⚪ Pending |
| M12 | Vercel deployment | ⚪ Pending |

No experiment is marked complete unless its artifact exists under `results/`
and passes the validation checks in `tests/`.

## Research questions

RQ1–RQ6 (BM25 vs. TF-IDF, dense vs. lexical, biomedical vs. general dense,
hybrid vs. individual retrievers, reranking's effect on top-ranked
effectiveness, and effectiveness/efficiency trade-offs) are stated in full in
[paper/methodology.md](paper/methodology.md) along with the corresponding
hypotheses H1–H4, which are explicitly treated as hypotheses — not reported
as findings — until the relevant experiments complete and pass statistical
testing.

## Reproducibility

```bash
python scripts/reproduce.py --config configs/default.yaml
```

Runs dataset audit → TF-IDF → BM25 → BGE → MedCPT → hybrid → reranker →
evaluation → statistics → figures → web export, resuming from cached
artifacts where present. See [docs/reproducibility.md](docs/reproducibility.md).

## Research portal

Vercel deployment link will be added here once M12 completes. The portal
reads only exported, verified JSON/CSV artifacts from `results/` — it never
runs transformer models itself (see [docs/architecture.md](docs/architecture.md#design-decision-vercel-never-runs-the-transformer-models)).

## Citation

See [CITATION.cff](CITATION.cff).

## Scientific-integrity statement

This project reports only genuine experimental output. No metric, dataset
count, citation, or statistical result is fabricated. Pending experiments are
labeled `pending` (not filled with plausible-looking numbers); failed runs
are labeled `failed` with their error preserved, never silently replaced with
a guessed value. See `src/biomedical_ir/manifests.py` for the manifest schema
that every experiment run must satisfy.
