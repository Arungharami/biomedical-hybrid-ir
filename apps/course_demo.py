#!/usr/bin/env python3
"""CAP 6776 interactive demo: arbitrary-query BM25, MedCPT, and hybrid RRF.

Coding-aid scaffold: review, test, and explain this code before course submission.
Run from the repository root after completing scripts/audit_dataset.py.

    pip install -e .
    pip install gradio
    python apps/course_demo.py

MedCPT downloads model weights and builds the article index on first semantic
query. Warm up the semantic path before starting the recorded demonstration.
The app intentionally does not display qrel-based "relevant" badges for
arbitrary text queries, because those queries have no human judgments.
"""
from __future__ import annotations

from functools import lru_cache

import gradio as gr

from biomedical_ir.bm25 import BM25Retriever
from biomedical_ir.data import compose_document_text, load_nfcorpus_from_raw
from biomedical_ir.fusion import fuse_runs
from biomedical_ir.medcpt import MedCPTRetriever

CANDIDATE_DEPTH = 100
RRF_K = 60


@lru_cache(maxsize=1)
def load_lexical():
    """Read the audited collection and construct an inverted BM25 index once."""
    dataset = load_nfcorpus_from_raw("data/raw/nfcorpus")
    documents = {
        doc_id: compose_document_text(meta["title"], meta["text"])
        for doc_id, meta in dataset.corpus.items()
    }
    retriever = BM25Retriever().fit(documents)
    return dataset, retriever


@lru_cache(maxsize=1)
def load_semantic():
    """Build the biomedical dense index once per app process (expensive first call)."""
    dataset, _ = load_lexical()
    retriever = MedCPTRetriever()
    retriever.build_index(dataset.corpus)
    return retriever


def search(query: str, method: str, top_k: int):
    """Return ranked documents and scores for a user-entered query."""
    query = (query or "").strip()
    if not query:
        return []

    dataset, bm25 = load_lexical()
    depth = CANDIDATE_DEPTH
    if method in ("BM25", "Hybrid (RRF)"):
        bm25_hits = bm25.rank(query, top_k=depth)
    else:
        bm25_hits = []

    if method in ("MedCPT", "Hybrid (RRF)"):
        medcpt_hits = load_semantic().rank_all({"live": query}, top_k=depth)["live"]
    else:
        medcpt_hits = []

    if method == "BM25":
        hits = bm25_hits[: int(top_k)]
    elif method == "MedCPT":
        hits = medcpt_hits[: int(top_k)]
    elif method == "Hybrid (RRF)":
        # Ranks, not incomparable BM25/dense raw scores, are fused.
        hits = fuse_runs(
            [{"live": bm25_hits}, {"live": medcpt_hits}],
            k=RRF_K,
            candidate_depth=depth,
            top_k=int(top_k),
        )["live"]
    else:
        raise ValueError(f"Unknown retrieval method: {method}")

    output = []
    for rank, (doc_id, score) in enumerate(hits, start=1):
        meta = dataset.corpus[doc_id]
        output.append([
            rank,
            doc_id,
            round(float(score), 5),
            meta.get("title", ""),
            meta.get("text", "")[:300],
        ])
    return output


def main():
    with gr.Blocks(title="CAP 6776 | Biomedical Hybrid IR Demo") as demo:
        gr.Markdown(
            "# Biomedical Information Retrieval — Live Demo\n"
            "Enter any query, compare lexical and semantic retrieval, and inspect "
            "hybrid Reciprocal Rank Fusion. The initial MedCPT search loads model "
            "weights and builds an index; initialize it before recording."
        )
        query = gr.Textbox(
            label="Biomedical query",
            placeholder="e.g. What is the role of diet in coronary heart disease?",
            value="salmon",
        )
        with gr.Row():
            method = gr.Dropdown(
                ["BM25", "MedCPT", "Hybrid (RRF)"],
                value="BM25",
                label="Retrieval method",
            )
            top_k = gr.Slider(1, 20, value=5, step=1, label="Top results")
        run = gr.Button("Search", variant="primary")
        table = gr.Dataframe(
            headers=["Rank", "Document ID", "Score", "Title", "Snippet"],
            datatype=["number", "str", "number", "str", "str"],
            label="Ranked results",
            interactive=False,
        )
        run.click(search, inputs=[query, method, top_k], outputs=table)
        query.submit(search, inputs=[query, method, top_k], outputs=table)
        gr.Examples(
            examples=[
                ["salmon", "BM25", 5],
                ["Exploiting Autophagy to Live Longer", "MedCPT", 5],
                ["canker sores", "Hybrid (RRF)", 5],
                ["Fosamax", "Hybrid (RRF)", 5],
                ["What's Driving America's Obesity Problem?", "Hybrid (RRF)", 5],
            ],
            inputs=[query, method, top_k],
        )
        gr.Markdown(
            "Educational research system, not medical advice. "
            "Scores across different retrieval methods are not directly comparable."
        )
    demo.launch()


if __name__ == "__main__":
    main()
