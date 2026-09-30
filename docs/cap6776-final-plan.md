# CAP 6776 Final Project — course-ready completion plan

**Student:** Arun Kumar Gharami  
**Course:** CAP 6776 Information Retrieval, Fall 2026  
**Deadline:** November 8, 2026  
**Working title:** Biomedical Hybrid Information Retrieval with BM25, MedCPT and Reciprocal Rank Fusion

> This plan is a course-specific working checklist. The research repository already contains
> real saved experiment outputs. The Gradio app and five-query evaluator on this
> branch are new AI-assisted coding scaffolds: the student must run, test,
> understand and adapt them before using them in the individual submission.
> No claim is made here that the new Gradio app has been executed successfully.

## 1. Domain and task

Retrieve relevant biomedical/NutritionFacts/PubMed documents for natural-language
queries. NFCorpus has 3,633 documents, 3,237 queries overall, and 323 queries
in its held-out test qrels. The original dataset's judgments are graded
0/1/2. All final evaluation must use the official **test** qrels; tuning
must not occur against that split.

## 2. Retrieval architecture

1. Load the corpus; compose title and body for lexical retrieval.
2. Preprocess and build the BM25 inverted index using the existing
   `BM25Retriever.fit` and `rank` methods.
3. Use the original MedCPT query/article encoders and FAISS dense index
   (`MedCPTRetriever.build_index` / `rank_all`).
4. Fuse BM25 and MedCPT's rankings by RRF with k=60.
5. Optionally demonstrate previously executed MedCPT cross-encoder reranking
   from saved experiment outputs; it is *not* part of the new live Gradio app.
6. Return ranked document ID, title, snippet and the method-specific score.
   Do not treat scores from different retrieval methods as directly comparable.

## 3. Run and validate

From the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
pip install gradio
python -m pytest -q
python scripts/audit_dataset.py
python apps/course_demo.py
```

On Windows, activate with `.venv\\Scripts\\activate`. The first semantic
query downloads/loads MedCPT weights and builds the dense article index.
Warm up **MedCPT** and **Hybrid (RRF)** before beginning the recording.
Do not call the Vercel portal a live inference endpoint: its search-demo
page explicitly uses precomputed research output.

If the model is too demanding for the recording machine, run the live
app on a sufficiently provisioned machine and retain the precomputed
web portal for stable side-by-side model comparisons.

## 4. At least five queries with existing judgments

These are real NFCorpus test examples shown in the existing error analysis.
**The listed document is one judged relevant example per query, not the
complete qrels set.** The evaluator uses **all** available judgments per
query from `qrels_test.json`.

| Query ID | Query | Example judged relevant document | Grade |
|---|---|---|---:|
| PLAIN-2040 | salmon | MED-3024 | 1 |
| PLAIN-12 | Exploiting Autophagy to Live Longer | MED-2514 | 1 |
| PLAIN-817 | canker sores | MED-4841 | 1 |
| PLAIN-1214 | Fosamax | MED-2990 | 1 |
| PLAIN-33 | What's Driving America's Obesity Problem? | MED-2715 | 2 |

Run:

```bash
python scripts/evaluate_five.py
```

The script computes per-query and average **P@10** and **nDCG@10** for the
six previously executed models wherever their run JSON exists. The output
must be captured in a table or screenshot and explained in the video.
Do not invent missing metric values or substitute the one example
judgment above for full qrels.

## 5. Existing full test-set results (n=323; from saved real artifacts)

| Model | P@10 | nDCG@10 |
|---|---:|---:|
| TF-IDF | 0.2167 | 0.3050 |
| BM25 | 0.2071 | 0.2954 |
| BGE | 0.2796 | 0.3712 |
| MedCPT | 0.2697 | 0.3654 |
| BM25 + MedCPT (RRF) | 0.2598 | 0.3620 |
| Hybrid + MedCPT reranker (candidate pool 50) | 0.2765 | 0.3731 |

The reranked nDCG@10 point estimate exceeds Hybrid RRF's, but the paired
bootstrap comparison was **not significant** (reported p=0.194). Reranking
also adds material latency. Hybrid RRF is **not** uniformly better than
either individual dense retriever. These limitations are useful in the
course interpretation; do not hide them.

The reranker's pool size is 50, so Recall@100 and MAP for that run are
candidate-pool-limited and should not be presented as a like-for-like
top-100 comparison without the caveat.

## 6. Show and explain the IR concepts

- **Indexing:** inverted postings, document length, document frequency and
  IDF for BM25; FAISS dense index for MedCPT.
- **Ranking:** BM25 term frequency saturation/length normalization;
  MedCPT vector similarity; RRF rank fusion `sum(1/(60+rank))`.
- **Advanced technique:** actually demonstrate hybrid RRF on an arbitrary
  query in the Gradio app, then explain why rank fusion avoids adding
  incomparable BM25 and dense scores.
- **Evaluation:** explain that P@10 is the fraction of relevant documents
  in the top ten; nDCG@10 rewards putting higher-grade judgments earlier.
- **Error analysis:** show where lexical search beats dense (e.g. salmon),
  where dense recovers lexical misses (e.g. autophagy or Fosamax), and
  where reranking changes top results.

## 7. Presentation storyboard — exactly 15 minutes

| Time | Topic |
|---|---|
| 0:00–1:30 | Domain, problem and search objective |
| 1:30–3:30 | NFCorpus dataset, corpus size and official qrels |
| 3:30–6:30 | Indexing, BM25, MedCPT, RRF architecture and key code |
| 6:30–10:30 | Live BM25/MedCPT/Hybrid queries and result comparison |
| 10:30–13:00 | Five judged queries; P@10/nDCG@10; full test-set result table |
| 13:00–14:00 | Error cases, latency and limitations |
| 14:00–15:00 | Conclusion, reproducibility and AI-use disclosure |

Record the running system **and** show a short code walkthrough. Upload
the final recording to YouTube (unlisted is fine when allowed) or Google
Drive with link access set for the instructor, and submit the working
video link through Canvas.

## 8. Suggested checkpoints

- By October 4: reproduce tests and dataset audit.
- By October 11: run the Gradio app with an arbitrary BM25 query.
- By October 18: initialize MedCPT, verify hybrid RRF and record trial queries.
- By October 25: run five-query evaluation; capture outputs; prepare comparison slide.
- By November 1: complete all slides and rehearse 15-minute walkthrough.
- By November 5: record, review audio/screens and verify the video link.
- By November 7: submit via Canvas, leaving buffer before November 8 deadline.

## 9. AI disclosure reminder

Example to adapt truthfully: “I used AI assistance for development guidance,
code suggestions, debugging and presentation planning. I reviewed the code,
ran the experiments, verified the results, and am responsible for the
implementation, explanation and final analysis.” Only claim steps that
you actually performed and verified.

The individual-work policy remains authoritative: own the final code,
writing, experimental choices and analysis; do not submit unreviewed
AI-generated work as if you personally implemented and validated it.
