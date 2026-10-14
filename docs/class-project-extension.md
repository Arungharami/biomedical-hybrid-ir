# CAP 6776 class-project extension
Instructor: Juan D. Yepes. Project: Biomedical Hybrid IR + Patient Experience Analysis.

## Scope and research questions
Keep NFCorpus TF-IDF, BM25, BGE, MedCPT, RRF and reranking as the graded IR core.
RQ1: When do lexical and biomedical dense rankings complement each other?
RQ2: Does reranking improve nDCG@10 enough to justify latency?
RQ3 (extension): How well does a general pretrained sentiment model transfer to patient reviews compared with an in-domain TF-IDF/LR baseline?

Sentiment is separate metadata for a future patient-review search tab. Never use a positive sentiment score as evidence of relevance, medical truth, drug effectiveness or safety. NFCorpus has relevance judgments, not sentiment labels. Drug reviews have rating-derived satisfaction proxies, not IR judgments.

## Implemented pipeline
1. Hugging Face drug-review download at a resolved commit SHA.
2. HTML entity decoding, whitespace normalization, invalid-row auditing.
3. Exact normalized-text deduplication; remove official-test overlap with training.
4. Stratified train/dev split within official training; official test remains held out.
5. Seeded subsets for affordable classroom runs (10k train, 1k dev/test by default).
6. Train TF-IDF/LR; select C from 0.1, 1, 10 using dev macro-F1.
7. Optional Twitter-domain RoBERTa transfer baseline on the identical test subset.
8. Export per-class precision/recall/F1, macro-F1, accuracy, confusion matrix, prediction time, hashes, package versions and SHA provenance.
9. Keep outputs under results/sentiment, separate from existing retrieval metrics.

Run:
```bash
pip install -r requirements.txt
pip install -e .
python scripts/run_sentiment.py
python scripts/run_sentiment.py --transformer --output results/sentiment-transformer
```
Do not compare metrics from different subsets or budgets. Sentiment thresholds (1–4/5–6/7–10) are a proposed labeling policy. Report that policy and manually audit a small sample for label/text disagreement. Ratings must never enter model features. Exact deduplication cannot guarantee independent patients or eliminate near duplicates. Pretrained training-data overlap is unknown. Transformer input is truncated to 512 tokens; measure long-review errors. No clinical claims.

## Hugging Face registry
| Asset | Purpose | Implementation |
|---|---|---|
| BeIR/nfcorpus + BeIR/nfcorpus-qrels | Primary retrieval benchmark | Existing pipeline |
| BAAI/bge-base-en-v1.5 | General dense encoder | Existing pipeline |
| ncbi/MedCPT-Query-Encoder + Article-Encoder | Biomedical dual encoder | Existing pipeline |
| ncbi/MedCPT-Cross-Encoder | Reranking | Existing pipeline |
| lewtun/drug-reviews | Review/rating experiment | New runner |
| cardiffnlp/twitter-roberta-base-sentiment-latest | General three-class transfer baseline | Optional new runner |
| BeIR/scifact + BeIR/scifact-qrels | Scientific-claim retrieval replication | Planned; needs generic loader and separate split audit |

Dataset licensing and original-source terms need review before redistribution. Drug-review Hub page lacks an explicit license in the inspected metadata; do not upload raw reviews in this branch. The runner exports only hashes and predictions.

## Kaggle workflow
Upload notebooks/Kaggle_Biomedical_IR_Sentiment.ipynb to Kaggle. Enable Internet. CPU is enough for LR; GPU is useful for transformer and dense retrieval. The notebook checks Python compatibility (3.11 or 3.12), clones this branch to /kaggle/working, installs dependencies, and runs reusable scripts. Enable the expensive cells intentionally. Kaggle execution has NOT been performed by this change.

The existing repo ships historical results, so fresh retrieval experiments MUST use reproduce.py --force. Otherwise the orchestrator skips them. Back up outputs to a zip under /kaggle/working and download after execution. Full retrieval uses existing script configuration; GPU availability is not a guarantee of GPU selection. Read each generated manifest.

## Data branch and collaboration
Branch: data/hf-kaggle-sentiment. Store schema/manifest code and notebooks in Git.
Store downloaded data, embeddings, weights and caches outside Git. Commit only reviewed summaries and plots with provenance; use Kaggle outputs or private storage for large artifacts. Do not overwrite historical NFCorpus results with sentiment outputs.

## Prioritized additional topics
1. SciFact replication: adapt ingestion, validate qrels and split availability, run the same six retrieval methods. Do not invent a dev split if unavailable; pre-register hyperparameters or document a training-only holdout.
2. Ablations: tune BM25 k1/b, RRF k, and reranking pool size only on dev; compare under fixed candidate budgets.
3. Entity-aware search: medical condition/drug entity extraction; evaluate entities independently and compare search with/without expansion.
4. Sentiment facets: query reviews by condition and predicted sentiment. Before claiming retrieval gains, create independently judged queries/qrels with blind human assessment.
5. RAG: cite retrieved abstracts, measure retrieval and answer grounding separately, include abstention. No diagnosis or treatment recommendations.

## Class deliverables
Architecture diagram; indexing/ranking equations; Kaggle notebook; IR results table with MAP/MRR/nDCG/Recall and latency; separate sentiment confusion matrix; query-level error cases; dataset/model cards; limitations; reproducibility manifests. Show original verified results and newly executed extensions distinctly.

## Status
Code and notebook added; offline tests are the verification record for this change.
Remote HF downloads, transformer inference, Kaggle execution and new experiment metrics remain pending until actually run.

## Sources
- https://huggingface.co/datasets/BeIR/nfcorpus
- https://huggingface.co/datasets/BeIR/scifact
- https://huggingface.co/datasets/lewtun/drug-reviews
- https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest
- https://huggingface.co/learn/llm-course/chapter5/3
- https://www.kaggle.com/docs/notebooks
