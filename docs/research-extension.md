# Research extension following Professor Dingding Wang's feedback

Proposed title: **When Does Lexical–Dense Fusion Improve Biomedical Retrieval? A Multi-Benchmark Study with Validated Hyperparameters and Statistical Evaluation.**

This branch implements the experiment infrastructure. It does not claim new benchmark results. Existing NFCorpus results retain their original provenance; sentiment is a separate class extension.

## Mapping feedback to implementation
| Requested improvement | Added implementation |
|---|---|
| More benchmarks | Pinned Hugging Face loaders for NFCorpus, SciFact and TREC-COVID |
| Validation studies | BM25 grid search; RRF and weighted-fusion tuning; optional shared rerank-pool study |
| Fusion versus single methods | TF-IDF, BM25, BGE, MedCPT, BM25+BGE and BM25+MedCPT under two fusion rules |
| Evaluation rigor | Query-level bootstrap intervals, paired Monte Carlo sign-randomization tests, per-dataset and study-wide Holm correction |

## Benchmark partitions
- **NFCorpus:** preserve official validation as dev.
- **SciFact:** preserve official test; reserve 20% of official training query IDs for development, seed 42. This is a proposed holdout, not an official SciFact dev split.
- **TREC-COVID:** no artificial split of test. Supply selection.json from another benchmark; transfer its BM25/fusion settings and pinned model SHAs. If reranking is enabled, transfer its selected common pool too.
- Data loader fails on duplicate IDs, duplicate judgments, dangling references, empty text, fractional/negative relevance, overlapping split query IDs and normalized dev/test query-text overlap.
- Corpus documents may appear in judgments across query splits; the split unit is the query. This is an evaluation of pretrained retrieval, not supervised training on the test judgments.
- Dataset and qrels commit SHAs, split IDs, holdout policy and query-text overlap counts are saved.

SciFact and TREC-COVID are replication benchmarks for pretrained models, not necessarily contamination-free unseen datasets. Investigate each model's training and evaluation history before claiming zero-shot novelty.

## Models and budgets
Default candidate depth: 100 per single retriever.
- TF-IDF: existing baseline configuration, fixed.
- BM25: k1 in {0.6, 1.2, 1.8}; b in {0.25, 0.5, 0.75}; select dev nDCG@10.
- BGE and MedCPT: reuse existing encoder/index classes; download model files at resolved Hub commit SHAs.
- RRF: k in {10, 30, 60, 100}.
- Weighted fusion: lexical alpha in {0, .25, .5, .75, 1}; independently min-max normalize each query's top-100 component scores, assign missing documents zero. Equal-score observed documents receive normalized value 1. Alpha endpoints reproduce the active component.
- Each fusion gets up to 200 unique input candidates and returns 100. This is an explicit extra retrieval cost; single methods return 100. Do not claim equal computational cost.
- Optional MedCPT cross-encoder: pools {20, 50, 100}; select a COMMON pool by mean dev nDCG across all seven candidate sources (BM25, both dense systems, all four fusion systems). Apply the same selected pool to every test candidate source.
- TF-IDF reranking and additional fusion families are outside this version's comparison set. “All methods” refers to the declared experiment matrix, not every fusion algorithm in the literature.

Selection traces and frozen settings are written before computing test metrics. Tied dev scores select the first grid value deterministically. No transformer fine-tuning is performed.

## Metrics and inference
Use the existing pytrec_eval evaluator for real benchmark outputs.
- Primary: nDCG@10, using the project's TREC linear graded-gain convention.
- Supporting: P@10, Recall@100, MAP@100, MRR@10; all existing metrics are also retained.
- MAP is limited by available retrieved rankings. Pool-limited reranker Recall@100/MAP should not be interpreted as full-depth effectiveness.
- Preserve every official judged test query; missing component query coverage is an error, not a smaller denominator.
- Report pointwise 95% percentile bootstrap intervals for each system's mean primary score and each paired primary improvement.
- Two-sided paired Monte Carlo sign-randomization p-values with plus-one correction; 10,000 resamples and seed 42.
- Planned family: each of four fusion systems versus BM25 and its dense ingredient (8 contrasts). With reranking, add seven reranker-versus-source contrasts (15 total).
- Holm-adjust all planned primary contrasts per dataset. summarize_research.py additionally corrects the complete primary family across supplied benchmark runs.
- Supporting metrics are descriptive in this version; no uncorrected inferential claims for them.
- Confidence intervals are pointwise, not simultaneous intervals. A positive estimate alone is not a significant improvement.
- Query-length <=8/>8 whitespace tokens and top-10 Jaccard ranking overlap <=.2/>.2 are predefined descriptive strata. The subgroup report contains mean fusion-versus-dense gain and wins/losses; no subgroup significance claims.
- Peak RSS is cumulative process memory, excluding GPU memory. Stage timings include lexical indexing/querying, dense indexing/querying, fusion only, and reranking only; they are not end-to-end interactive latency.

## Run locally or in Kaggle
Python 3.11 or 3.12, Internet access, package installation, and optional GPU are required.
```bash
pip install -r requirements.txt
pip install -e .
python scripts/run_research.py --dataset nfcorpus --device cuda
python scripts/run_research.py --dataset scifact --device cuda
# Replace SOURCE below with the real completed NFCorpus run directory.
python scripts/run_research.py --dataset trec-covid --device cuda --frozen-selection SOURCE/selection.json
```
Add --rerank consistently to all three runs for the complete reranking study. TREC-COVID must receive a source selection produced with reranking enabled.
```bash
python scripts/summarize_research.py NFCORPUS_RUN SCIFACT_RUN TREC_COVID_RUN
```
Aggregation refuses incomplete runs, duplicate benchmark entries, incompatible model SHAs, different system sets and different candidate budgets. Rerank pool sizes may differ across independently tuned benchmarks; record them when interpreting results.

Every invocation creates a timestamped folder under results/research/DATASET/. No historical portal or paper results are overwritten.
Outputs: manifest.json, selection.json, report.json, summary.csv and run-SYSTEM.json. A failed run saves status=failed and its error. Use only complete runs in reports.

## Git and Kaggle
Branch: research/multibenchmark-fusion-validation.
Notebook: notebooks/Kaggle_MultiBenchmark_Research.ipynb.
Kaggle notebook clones this branch into a fresh work folder, installs packages, runs offline checks, then runs NFCorpus and SciFact. TREC-COVID and reranking are optional explicit switches due to their cost.
Raw data, caches, model weights and embeddings stay outside Git. Commit only reviewed derived summaries with manifests. Export the results zip from Kaggle after execution. There is no automatic publishing or account-token handling.

## Validation record
26 offline unittest cases pass: schema and split safety, normalized score fusion, fixed-setting transfer, Holm adjustment, paired inference, selection logic, notebook code compilation, cross-dataset aggregation, and full synthetic orchestration with real lexical models and mocked dense/reranker inference. Synthetic judgments are evaluated with the existing educational nDCG implementation solely for offline tests.
The production evaluator remains pytrec_eval. Full remote benchmark downloads, model inference, Kaggle execution, and the existing full pytest/ruff suite have not run in this environment because required packages/network access are unavailable. CI is configured separately to run checks on this pull request.

## Next research work
1. Execute NFCorpus and SciFact; inspect failed manifests and query overlaps.
2. Execute identical-budget reranking studies if compute permits.
3. Transfer frozen settings to TREC-COVID.
4. Aggregate the planned primary contrasts across datasets.
5. Review lexical/dense disagreement and fusion failure cases.
6. Update paper tables, figures and portal only with verified outputs.
7. Review prior fusion literature and establish the contribution before submission. Infrastructure and more experiments alone do not guarantee novelty or publication.

## Sources checked
- https://github.com/beir-cellar/beir
- https://huggingface.co/datasets/BeIR/nfcorpus
- https://huggingface.co/datasets/BeIR/scifact-qrels
- https://huggingface.co/datasets/BeIR/trec-covid-qrels
- https://github.com/ncbi/MedCPT
- https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html
- https://www.kaggle.com/docs/notebooks

