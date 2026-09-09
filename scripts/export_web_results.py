#!/usr/bin/env python
"""M11: export compact, real JSON artifacts for the Next.js research portal
(Section 36 of the project spec). Reads only already-verified results/ and
data/processed/ artifacts -- never fabricates a number. The portal
(web/app/) reads these files at build time; it never runs a model itself
(Section 35 -- see docs/architecture.md).

Produces, under web/data/:
    dataset.json        research-status.json   models.json
    experiments.json     metrics.json           comparison.json
    error-analysis.json  efficiency.json        search-demo.json

Usage:
    python scripts/export_web_results.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from biomedical_ir.data import load_nfcorpus_from_raw  # noqa: E402
from biomedical_ir.evaluation import load_run_json  # noqa: E402

# A curated set of real test queries for the /search demo (Section 37).
# Chosen to illustrate different real phenomena documented elsewhere on the
# portal -- every ranking shown for these is genuine, precomputed pipeline
# output (results/runs/*.json), never a live model call.
SEARCH_DEMO_QUERY_IDS = [
    "PLAIN-2040",  # "salmon" -- BM25 exact-match win, MedCPT miss (see error-analysis)
    "PLAIN-12",  # MedCPT recovers where BM25 misses entirely
    "PLAIN-1008",  # "deafness" -- BM25 zero-vocabulary-overlap failure
    "PLAIN-33",  # appears in both BM25-wins and MedCPT-wins examples
    "PLAIN-2490",
    "PLAIN-227",
    "PLAIN-133",
]

DATA_PROCESSED = REPO_ROOT / "data" / "processed"
RESULTS = REPO_ROOT / "results"
WEB_DATA = REPO_ROOT / "web" / "data"

MODELS_META = [
    {
        "id": "tfidf",
        "name": "TF-IDF",
        "family": "Classical lexical",
        "huggingface": None,
        "description": "scikit-learn TfidfVectorizer (sublinear TF, L2 norm, smoothed IDF) + cosine similarity.",
        "config": "configs/tfidf.yaml",
    },
    {
        "id": "bm25",
        "name": "BM25",
        "family": "Classical lexical",
        "huggingface": None,
        "description": "From-scratch Okapi BM25 (k1=1.2, b=0.75, frozen literature defaults). Robertson/Sparck-Jones IDF.",
        "config": "configs/bm25.yaml",
    },
    {
        "id": "bge",
        "name": "BGE",
        "family": "General dense retrieval",
        "huggingface": "BAAI/bge-base-en-v1.5",
        "description": "CLS pooling, L2-normalized embeddings, query-only instruction prefix. FAISS IndexFlatIP.",
        "config": "configs/bge.yaml",
    },
    {
        "id": "medcpt",
        "name": "MedCPT",
        "family": "Biomedical dense retrieval",
        "huggingface": "ncbi/MedCPT-Query-Encoder + ncbi/MedCPT-Article-Encoder",
        "description": "Two-tower biomedical retriever, CLS pooling, no normalization (raw dot product). Articles as [title, text] pairs.",
        "config": "configs/medcpt.yaml",
    },
    {
        "id": "hybrid_rrf",
        "name": "BM25 + MedCPT (RRF)",
        "family": "Hybrid retrieval",
        "huggingface": None,
        "description": "Reciprocal Rank Fusion of BM25 and MedCPT rankings, k=60. Operates on rank positions, not raw scores.",
        "config": "configs/hybrid.yaml",
    },
    {
        "id": "hybrid_reranked",
        "name": "Hybrid + MedCPT Cross-Encoder",
        "family": "Biomedical reranking",
        "huggingface": "ncbi/MedCPT-Cross-Encoder",
        "description": "Reranks the hybrid RRF run's top candidates (default pool=50) with a biomedical cross-encoder.",
        "config": "configs/reranker.yaml",
    },
]

# Mirrors the README's Experiment status table -- the one piece of this
# export that is necessarily hand-maintained (milestone status is a project
# fact, not a Python-computable artifact), kept in sync deliberately.
RESEARCH_STATUS = [
    {"milestone": "M0", "description": "Repository foundation, packaging, configs, CI skeleton", "status": "complete"},
    {"milestone": "M1", "description": "Dataset ingestion + validation", "status": "complete"},
    {"milestone": "M2", "description": "TF-IDF + BM25 baselines", "status": "complete"},
    {"milestone": "M3", "description": "BGE general dense retrieval", "status": "complete"},
    {"milestone": "M4", "description": "MedCPT biomedical dense retrieval", "status": "complete"},
    {"milestone": "M5", "description": "Hybrid RRF", "status": "complete"},
    {"milestone": "M6", "description": "MedCPT cross-encoder reranking", "status": "complete"},
    {"milestone": "M7", "description": "Full evaluation, statistical tests, efficiency analysis", "status": "complete"},
    {"milestone": "M8", "description": "Error analysis", "status": "complete"},
    {"milestone": "M9", "description": "Colab notebooks", "status": "complete"},
    {"milestone": "M10", "description": "Paper artifacts (figures, BibTeX)", "status": "complete"},
    {"milestone": "M11", "description": "Next.js research portal", "status": "complete"},
    {"milestone": "M12", "description": "Vercel deployment", "status": "in_progress"},
]


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    print(f"[export_web_results] wrote {path.relative_to(REPO_ROOT)}")


def export_dataset() -> None:
    payload = json.loads((DATA_PROCESSED / "dataset_stats.json").read_text())
    payload["corpus_detail"] = json.loads((DATA_PROCESSED / "corpus_stats.json").read_text())
    payload["query_detail"] = json.loads((DATA_PROCESSED / "query_stats.json").read_text())
    write_json(WEB_DATA / "dataset.json", payload)


def export_models() -> None:
    write_json(WEB_DATA / "models.json", MODELS_META)


def export_experiments() -> None:
    manifests = []
    for path in sorted((RESULTS / "manifests").glob("*.json")):
        manifests.append(json.loads(path.read_text()))
    write_json(WEB_DATA / "experiments.json", manifests)


def export_metrics() -> None:
    metrics = {}
    for model in ["tfidf", "bm25", "bge", "medcpt", "hybrid_rrf", "hybrid_reranked"]:
        path = RESULTS / "metrics" / f"{model}.json"
        metrics[model] = json.loads(path.read_text())
    ablation_path = RESULTS / "metrics" / "reranker_pool_ablation.json"
    if ablation_path.exists():
        metrics["reranker_pool_ablation"] = json.loads(ablation_path.read_text())
    write_json(WEB_DATA / "metrics.json", metrics)


def export_comparison() -> None:
    rows = []
    with open(RESULTS / "tables" / "main_results.csv") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    stats = json.loads((RESULTS / "tables" / "statistical_tests.json").read_text())
    write_json(WEB_DATA / "comparison.json", {"main_results": rows, "statistical_tests": stats})


def export_error_analysis() -> None:
    payload = json.loads((RESULTS / "error-analysis" / "error_analysis.json").read_text())
    write_json(WEB_DATA / "error-analysis.json", payload)


def export_efficiency() -> None:
    payload = json.loads((RESULTS / "tables" / "efficiency.json").read_text())
    write_json(WEB_DATA / "efficiency.json", payload)


def export_research_status() -> None:
    write_json(WEB_DATA / "research-status.json", RESEARCH_STATUS)


def export_search_demo(top_k: int = 5) -> None:
    """Real top-k rankings for a curated set of test queries, across all six
    models -- genuine precomputed pipeline output for the /search demo page.
    """
    data = load_nfcorpus_from_raw(REPO_ROOT / "data" / "raw" / "nfcorpus")
    runs = {
        model: load_run_json(RESULTS / "runs" / f"{model}.json")
        for model in ["bm25", "medcpt", "hybrid_rrf", "hybrid_reranked"]
    }

    demo = []
    for qid in SEARCH_DEMO_QUERY_IDS:
        if qid not in data.queries:
            continue
        entry = {"query_id": qid, "query": data.queries[qid], "results": {}}
        for model, run in runs.items():
            docs = run.get(qid, [])[:top_k]
            entry["results"][model] = [
                {
                    "doc_id": doc_id,
                    "score": score,
                    "title": data.corpus.get(doc_id, {}).get("title", ""),
                    "snippet": (data.corpus.get(doc_id, {}).get("text", "") or "")[:200],
                    "relevant": data.qrels.get("test", {}).get(qid, {}).get(doc_id, 0) > 0,
                }
                for doc_id, score in docs
            ]
        demo.append(entry)

    write_json(WEB_DATA / "search-demo.json", demo)


def main() -> int:
    WEB_DATA.mkdir(parents=True, exist_ok=True)
    export_dataset()
    export_models()
    export_experiments()
    export_metrics()
    export_comparison()
    export_error_analysis()
    export_efficiency()
    export_research_status()
    export_search_demo()
    print(f"\n[export_web_results] done -- {len(list(WEB_DATA.glob('*.json')))} files in {WEB_DATA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
