# Dataset: NFCorpus (via BeIR)

## Source

- **Corpus + queries:** [`BeIR/nfcorpus`](https://huggingface.co/datasets/BeIR/nfcorpus) on Hugging Face, configs `corpus` and `queries`.
- **Qrels:** [`BeIR/nfcorpus-qrels`](https://huggingface.co/datasets/BeIR/nfcorpus-qrels), splits `train` / `validation` / `test`.

These are the canonical BEIR-formatted release of the original NFCorpus
dataset (Boteva et al., 2016), a biomedical/nutrition information retrieval
collection built from NutritionFacts.org documents and PubMed articles.

## Verified structure (checked empirically against the live Hub, 2026-09-09)

```
BeIR/nfcorpus, config "corpus":  {_id, title, text}       -- 3,633 rows
BeIR/nfcorpus, config "queries": {_id, title, text}       -- 3,237 rows
BeIR/nfcorpus-qrels:             {query-id, corpus-id, score} split into
                                  train (110,575 raw rows / 2,590 unique queries),
                                  validation (11,385 raw rows / 324 unique queries),
                                  test (12,334 raw rows / 323 unique queries)
```

Two details worth flagging because they are easy to get wrong from
documentation alone (Section 41 of the project spec: never guess):

1. **The Hugging Face split name is `validation`, not `dev`.** This project's
   internal terminology (and the spec's) calls it "dev" — see
   `HF_SPLIT_NAME` in `src/biomedical_ir/data.py` for the mapping.
2. **Relevance judgments are graded, not binary.** Observed scores include
   0, 1, and 2 (not just 0/1), consistent with the original NFCorpus
   annotation scheme (2 = highly relevant, 1 = partially relevant).

## Splits and their role (data leakage rule, Section 4)

| Split (internal name) | HF split name | Queries w/ qrels | Role |
|---|---|---:|---|
| train | `train` | 2,590 | development only — never used for final evaluation |
| dev | `validation` | 324 | parameter tuning / model selection only |
| test | `test` | 323 | **final evaluation only** |

Any BM25/RRF-k parameter tuning performed in this project uses the dev split
exclusively; final values are frozen (see `configs/bm25.yaml`,
`configs/hybrid.yaml`) before any test-set number is computed. This is
enforced by convention in the config files' `tuning.split: "dev"` fields, not
by a runtime guard — reviewers should check that `evaluate_all.py` /
`scripts/reproduce.py` only reads `configs/*.yaml`'s frozen values when
producing `results/tables/main_results.*`.

## Validation performed

`src/biomedical_ir/validation.py` (invoked by `scripts/audit_dataset.py`)
checks: duplicate document/query IDs, qrels referencing missing
documents/queries, empty query strings, empty documents, split ID overlap
(leakage), and relevance-label type consistency. On the real dataset (see
`data/processed/dataset_stats.json`), **all checks pass with zero errors and
zero warnings** — 0 duplicates, 0 missing references, 0 empty
queries/documents, 0 split overlap.

## Document composition for embedding models

Per `configs/default.yaml -> document_composition`, when both `title` and
`text` are non-empty, documents are composed as `"{title} [SEP] {text}"` for
TF-IDF/BM25's underlying text and as `[title, text]` pairs for MedCPT (per its
model card's expected input format). See `docs/models.md` for exactly how
each model consumes this.

## Regenerating the audit artifacts

```bash
python scripts/audit_dataset.py               # downloads via Hugging Face `datasets`
python scripts/audit_dataset.py --from-raw     # reuses data/raw/nfcorpus/, no network
```

Writes `data/processed/{dataset_stats,corpus_stats,query_stats}.json`.
