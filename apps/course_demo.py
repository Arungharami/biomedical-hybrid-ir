#!/usr/bin/env python3
"""CAP 6776 live demo: type any query, run BM25 / MedCPT / Hybrid RRF / Hybrid + cross-encoder.

Everything shown is computed live by the same library code used for the
recorded experiments (see biomedical_ir/live_search.py). Nothing is read
from precomputed result files.

Run from the repository root (after `python scripts/audit_dataset.py` has
downloaded NFCorpus into data/raw/nfcorpus):

    pip install -e . gradio
    python apps/course_demo.py            # local:  http://127.0.0.1:7860
    python apps/course_demo.py --share    # Colab:  prints a public *.gradio.live link

Tabs
  1. Live search      - one method, with each hit's BM25 rank / MedCPT rank so RRF is visible
  2. Compare methods  - the same query through all four methods side by side
  3. Judged queries   - official NFCorpus test queries scored LIVE against the qrels
                        (P@10, nDCG@10, RR@10) - evaluation happening on screen

First MedCPT use downloads ~2 x 440 MB of weights and encodes 3,633 articles
(about 1-3 min on a GPU / Apple M-series; longer on CPU). Article embeddings are
cached to data/cache/ so later launches start in seconds. Press "Warm up
models" before recording.
"""

from __future__ import annotations

import argparse
import json
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))  # works even without `pip install -e .`

import gradio as gr  # noqa: E402

from biomedical_ir.data import load_nfcorpus_from_raw  # noqa: E402
from biomedical_ir.live_search import (  # noqa: E402
    BM25,
    HYBRID,
    MEDCPT,
    METHODS,
    RERANK,
    LiveSearchEngine,
    judge_ranking,
)

RAW_DIR = ROOT / "data" / "raw" / "nfcorpus"
CACHE_DIR = ROOT / "data" / "cache"
FEATURED_QUERIES = ["PLAIN-2040", "PLAIN-12", "PLAIN-817", "PLAIN-1214", "PLAIN-33"]
GRADE_MARK = {2: "★★ highly relevant", 1: "★ relevant"}


# ---------------------------------------------------------------------------
# Model construction (lazy; cached article embeddings)
# ---------------------------------------------------------------------------


def build_medcpt(corpus: dict[str, dict[str, str]]):
    import numpy as np

    from biomedical_ir.faiss_index import FaissDenseIndex
    from biomedical_ir.medcpt import MedCPTRetriever

    retriever = MedCPTRetriever()
    emb_path = CACHE_DIR / "medcpt_article_embeddings.npy"
    ids_path = CACHE_DIR / "medcpt_article_ids.json"
    doc_ids = list(corpus.keys())
    if emb_path.exists() and ids_path.exists() and json.loads(ids_path.read_text()) == doc_ids:
        embeddings = np.load(emb_path)
        retriever.doc_ids = doc_ids
        retriever.index = FaissDenseIndex.build(doc_ids, embeddings)
        print(f"[demo] Loaded cached MedCPT article embeddings {embeddings.shape}")
    else:
        print(f"[demo] Encoding {len(doc_ids)} articles with MedCPT (one-time)...")
        embeddings = retriever.build_index(corpus)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        np.save(emb_path, embeddings)
        ids_path.write_text(json.dumps(retriever.doc_ids))
    return retriever


def build_reranker():
    from biomedical_ir.reranker import CrossEncoderReranker

    return CrossEncoderReranker()


@lru_cache(maxsize=1)
def get_state():
    if not (RAW_DIR / "corpus.jsonl").exists():
        raise SystemExit(
            f"NFCorpus not found at {RAW_DIR}. Run `python scripts/audit_dataset.py` first."
        )
    data = load_nfcorpus_from_raw(RAW_DIR)
    engine = LiveSearchEngine(
        data.corpus,
        dense_factory=lambda: build_medcpt(data.corpus),
        reranker_factory=build_reranker,
    )
    return data, engine


# ---------------------------------------------------------------------------
# Tab callbacks
# ---------------------------------------------------------------------------


def _fmt_rank(r):
    return "-" if r is None else str(r)


def live_search(query: str, method: str, top_k: int, pool: int):
    _, engine = get_state()
    res = engine.search(query, method, int(top_k), int(pool))
    rows = [
        [
            h.rank,
            h.doc_id,
            round(h.score, 4),
            _fmt_rank(h.bm25_rank),
            _fmt_rank(h.dense_rank),
            _fmt_rank(h.rrf_rank),
            h.title,
            h.snippet,
        ]
        for h in res.hits
    ]
    status = f"**{method}** - {len(res.hits)} results in **{res.latency_ms:,.1f} ms**"
    if res.notes:
        status += "\n\n" + "\n".join(f"- {n}" for n in res.notes)
    return status, rows


def compare_methods(query: str, top_k: int, pool: int):
    _, engine = get_state()
    results = {m: engine.search(query, m, int(top_k), int(pool)) for m in METHODS}
    rows = []
    for i in range(int(top_k)):
        row = [i + 1]
        for m in METHODS:
            hits = results[m].hits
            row.append(f"{hits[i].doc_id} - {hits[i].title}" if i < len(hits) else "")
        rows.append(row)
    timing = " | ".join(f"{m}: {results[m].latency_ms:,.0f} ms" for m in METHODS)
    notes = sorted({n for r in results.values() for n in r.notes})
    status = f"Latency - {timing}" + ("".join(f"\n\n- {n}" for n in notes) if notes else "")
    return status, rows


def judged_query(choice: str, pool: int):
    data, engine = get_state()
    qid = choice.split(" ", 1)[0]
    query = data.queries[qid]
    qrels = data.qrels["test"][qid]
    metric_rows, ranked_cols = [], {}
    for m in METHODS:
        res = engine.search(query, m, top_k=10, pool=int(pool))
        ids = [h.doc_id for h in res.hits]
        scores = judge_ranking(ids, qrels, k=10)
        metric_rows.append(
            [m, round(scores["P@10"], 3), round(scores["nDCG@10"], 3), round(scores["RR@10"], 3),
             round(res.latency_ms, 1)]
        )
        ranked_cols[m] = [
            f"{GRADE_MARK.get(qrels.get(h.doc_id, 0), '·')}  {h.doc_id}: {h.title[:70]}"
            for h in res.hits
        ]
    top_rows = [
        [i + 1] + [ranked_cols[m][i] if i < len(ranked_cols[m]) else "" for m in METHODS]
        for i in range(10)
    ]
    n_rel = sum(1 for g in qrels.values() if g > 0)
    header = (
        f"**{qid}** - \"{query}\"  \n"
        f"Official test qrels: **{n_rel}** documents judged relevant "
        f"({sum(1 for g in qrels.values() if g == 2)} graded 2). "
        "Unjudged documents count as non-relevant."
    )
    return header, metric_rows, top_rows


def warm_up(pool: int):
    _, engine = get_state()
    engine.search("vitamin D and bone health", RERANK, top_k=5, pool=int(pool))
    return "Models loaded and warmed up - live queries will now be fast."


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------


def build_ui() -> gr.Blocks:
    data, _ = get_state()
    test_qids = sorted(data.qrels.get("test", {}).keys())
    featured = [q for q in FEATURED_QUERIES if q in data.qrels.get("test", {})]
    ordered = featured + [q for q in test_qids if q not in featured]
    choices = [f"{q}  {data.queries.get(q, '')}" for q in ordered]

    with gr.Blocks(title="Biomedical Hybrid IR - Live Demo") as demo:
        gr.Markdown(
            "# Biomedical Hybrid Information Retrieval - live demo\n"
            f"NFCorpus: **{len(data.corpus):,}** PubMed-style documents · "
            "BM25 inverted index · MedCPT dense vectors (FAISS) · Reciprocal Rank Fusion (k=60) · "
            "MedCPT cross-encoder reranking. Educational system - not medical advice."
        )
        with gr.Row():
            pool = gr.Slider(10, 100, value=50, step=10, label="Rerank candidate pool")
            warm_btn = gr.Button("Warm up models")
            warm_msg = gr.Markdown()
        warm_btn.click(warm_up, inputs=pool, outputs=warm_msg)

        with gr.Tab("1 · Live search"):
            q = gr.Textbox(label="Query", value="does green tea lower cholesterol")
            with gr.Row():
                method = gr.Radio(list(METHODS), value=HYBRID, label="Method")
                top_k = gr.Slider(1, 20, value=10, step=1, label="Results")
            go = gr.Button("Search", variant="primary")
            status = gr.Markdown()
            table = gr.Dataframe(
                headers=["Rank", "Doc", "Score", "BM25 rank", "MedCPT rank", "RRF rank (pre-rerank)",
                         "Title", "Snippet"],
                wrap=True,
                interactive=False,
            )
            go.click(live_search, [q, method, top_k, pool], [status, table])
            q.submit(live_search, [q, method, top_k, pool], [status, table])
            gr.Examples(
                [["salmon", BM25], ["salmon", MEDCPT], ["Fosamax", BM25], ["Fosamax", HYBRID],
                 ["can diet reverse heart disease", RERANK]],
                [q, method],
            )

        with gr.Tab("2 · Compare methods"):
            q2 = gr.Textbox(label="Query", value="deafness")
            k2 = gr.Slider(1, 10, value=5, step=1, label="Results per method")
            go2 = gr.Button("Compare", variant="primary")
            status2 = gr.Markdown()
            table2 = gr.Dataframe(headers=["Rank", *METHODS], wrap=True, interactive=False)
            go2.click(compare_methods, [q2, k2, pool], [status2, table2])
            q2.submit(compare_methods, [q2, k2, pool], [status2, table2])

        with gr.Tab("3 · Judged test queries (live evaluation)"):
            pick = gr.Dropdown(choices, value=choices[0] if choices else None,
                               label="NFCorpus test query (first five = presentation set)")
            go3 = gr.Button("Run all four methods and score against qrels", variant="primary")
            header3 = gr.Markdown()
            metrics3 = gr.Dataframe(
                headers=["Method", "P@10", "nDCG@10", "RR@10", "Latency (ms)"], interactive=False
            )
            top3 = gr.Dataframe(headers=["Rank", *METHODS], wrap=True, interactive=False)
            go3.click(judged_query, [pick, pool], [header3, metrics3, top3])
    return demo


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--share", action="store_true", help="public link (needed on Colab)")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()
    build_ui().launch(share=args.share, server_port=args.port)


if __name__ == "__main__":
    main()
