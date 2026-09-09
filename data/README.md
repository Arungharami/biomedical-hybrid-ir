# data/

| Directory | Contents | In git? |
|---|---|---|
| `raw/` | Cached JSONL/JSON dump of NFCorpus as downloaded from Hugging Face (`scripts/download_data.py`) | No — regenerable, gitignored |
| `cache/` | Hugging Face `datasets`/`transformers` cache (arrow files, tokenizer files, model weights) | No — regenerable, gitignored |
| `processed/` | Small derived JSON artifacts: `dataset_stats.json`, `corpus_stats.json`, `query_stats.json` | **Yes** — these are the audit output referenced by the paper/portal |

Regenerate everything with:

```bash
python scripts/audit_dataset.py
```

No raw or cached data is committed to version control (see `.gitignore`);
only the small, derived statistics JSON files in `processed/` are tracked,
since those are cited directly in the paper and research portal.
