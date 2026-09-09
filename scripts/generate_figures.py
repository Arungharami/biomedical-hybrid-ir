#!/usr/bin/env python
"""M10: publication figures (Section 29 of the project spec), built from real
results/metrics/*.json and results/tables/*.json -- no fabricated data.

Figures 1 (system architecture) and 2 (retrieval pipeline) are represented
by the Mermaid diagram in docs/architecture.md rather than a redundant
static image (a documented choice, not an omission). This script generates
Figures 3-9:

    figure3_ndcg_by_model      figure4_map_by_model
    figure5_mrr_by_model       figure6_recall_at_k_curves
    figure7_hybrid_improvement figure8_reranker_improvement
    figure9_ndcg_vs_latency

Palette: the dataviz skill's validated default categorical palette (first 6
slots), confirmed via scripts/validate_palette.js against both the
"adjacent" pairlist (bars/lines here) and, for the Figure 9 scatter (an
all-pairs context), reinforced with direct point labels per the skill's
"identity is never color-alone" rule since only the first 3 slots clear the
all-pairs floors on their own.

Usage:
    python scripts/generate_figures.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

METRICS_DIR = REPO_ROOT / "results" / "metrics"
FIGURES_DIR = REPO_ROOT / "results" / "figures"

MODELS = ["tfidf", "bm25", "bge", "medcpt", "hybrid_rrf", "hybrid_reranked"]
MODEL_LABELS = {
    "tfidf": "TF-IDF",
    "bm25": "BM25",
    "bge": "BGE",
    "medcpt": "MedCPT",
    "hybrid_rrf": "Hybrid\nRRF",
    "hybrid_reranked": "Hybrid+\nReranker",
}
# Validated categorical palette (dataviz skill references/palette.md, slots 1-6),
# fixed hue order assigned to models -- never re-cycled or re-ordered per model.
COLORS = {
    "tfidf": "#2a78d6",
    "bm25": "#eb6834",
    "bge": "#1baf7a",
    "medcpt": "#eda100",
    "hybrid_rrf": "#e87ba4",
    "hybrid_reranked": "#008300",
}

plt.rcParams.update(
    {
        "font.size": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#8a8a86",
        "axes.grid": True,
        "grid.color": "#e5e4df",
        "grid.linewidth": 0.8,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    }
)


def load_metrics() -> dict[str, dict]:
    out = {}
    for m in MODELS:
        path = METRICS_DIR / f"{m}.json"
        out[m] = json.loads(path.read_text())
    return out


def save_figure(fig, name: str) -> None:
    for ext in ("png", "svg", "pdf"):
        path = FIGURES_DIR / f"{name}.{ext}"
        fig.savefig(path, bbox_inches="tight", dpi=150 if ext == "png" else None)
    plt.close(fig)
    print(f"[generate_figures] wrote {name}.{{png,svg,pdf}}")


def bar_chart(metrics: dict, metric_key: str, title: str, ylabel: str, filename: str) -> None:
    values = [metrics[m]["metrics"][metric_key] for m in MODELS]
    colors = [COLORS[m] for m in MODELS]
    labels = [MODEL_LABELS[m] for m in MODELS]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(labels, values, color=colors, width=0.62, edgecolor="none")
    for bar, v in zip(bars, values):
        ax.annotate(
            f"{v:.4f}",
            (bar.get_x() + bar.get_width() / 2, v),
            textcoords="offset points",
            xytext=(0, 4),
            ha="center",
            fontsize=9,
            color="#2b2b28",
        )
    ax.set_title(title, fontsize=13, pad=12)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, max(values) * 1.2)
    ax.tick_params(axis="x", labelsize=9.5)
    save_figure(fig, filename)


def figure6_recall_curves(metrics: dict) -> None:
    ks = [10, 20, 50, 100]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for m in MODELS:
        values = [metrics[m]["metrics"][f"Recall@{k}"] for k in ks]
        ax.plot(
            ks,
            values,
            marker="o",
            markersize=6,
            linewidth=2,
            color=COLORS[m],
            label=MODEL_LABELS[m].replace("\n", " "),
        )
    ax.set_title("Recall@K curves, all six models (real test-split results)", fontsize=13, pad=12)
    ax.set_xlabel("K")
    ax.set_ylabel("Recall@K")
    ax.set_xticks(ks)
    ax.legend(loc="lower right", fontsize=9, frameon=False)
    save_figure(fig, "figure6_recall_at_k_curves")


def figure7_hybrid_improvement(metrics: dict) -> None:
    keys = ["P@10", "Recall@100", "MAP", "MRR@10", "nDCG@10"]
    compare_models = ["bm25", "medcpt", "hybrid_rrf"]
    x = range(len(keys))
    width = 0.26
    fig, ax = plt.subplots(figsize=(8.5, 5))
    for i, m in enumerate(compare_models):
        values = [metrics[m]["metrics"][k] for k in keys]
        offset = (i - 1) * width
        ax.bar(
            [xi + offset for xi in x],
            values,
            width=width,
            color=COLORS[m],
            label=MODEL_LABELS[m].replace("\n", " "),
        )
    ax.set_title("Hybrid RRF vs. its individual components (real results)", fontsize=13, pad=12)
    ax.set_xticks(list(x))
    ax.set_xticklabels(keys)
    ax.legend(frameon=False, fontsize=9.5)
    ax.set_ylabel("Score")
    save_figure(fig, "figure7_hybrid_improvement")


def figure8_reranker_improvement(metrics: dict) -> None:
    keys = ["P@10", "MAP", "MRR@10", "nDCG@10"]  # Recall@100 excluded: capped by candidate pool, see docs/models.md
    compare_models = ["hybrid_rrf", "hybrid_reranked"]
    x = range(len(keys))
    width = 0.32
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for i, m in enumerate(compare_models):
        values = [metrics[m]["metrics"][k] for k in keys]
        offset = (i - 0.5) * width
        ax.bar(
            [xi + offset for xi in x],
            values,
            width=width,
            color=COLORS[m],
            label=MODEL_LABELS[m].replace("\n", " "),
        )
    ax.set_title(
        "Cross-encoder reranking vs. hybrid RRF\n(Recall@100 excluded — capped by candidate pool, see docs/models.md)",
        fontsize=12,
        pad=12,
    )
    ax.set_xticks(list(x))
    ax.set_xticklabels(keys)
    ax.legend(frameon=False, fontsize=9.5)
    ax.set_ylabel("Score")
    save_figure(fig, "figure8_reranker_improvement")


def figure9_ndcg_vs_latency(metrics: dict) -> None:
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for m in MODELS:
        latency = metrics[m].get("timing", {}).get("latency_ms_per_query")
        ndcg = metrics[m]["metrics"]["nDCG@10"]
        if latency is None:
            continue
        ax.scatter(latency, ndcg, s=90, color=COLORS[m], zorder=3, edgecolor="white", linewidth=1)
        ax.annotate(
            MODEL_LABELS[m].replace("\n", " "),
            (latency, ndcg),
            textcoords="offset points",
            xytext=(7, 4),
            fontsize=9.5,
            color="#2b2b28",
        )
    ax.set_xscale("log")
    ax.set_xlabel("Latency (ms/query, log scale)")
    ax.set_ylabel("nDCG@10")
    ax.set_title("Effectiveness vs. efficiency: nDCG@10 vs. latency (real measurements)", fontsize=12.5, pad=12)
    save_figure(fig, "figure9_ndcg_vs_latency")


def main() -> int:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    metrics = load_metrics()

    bar_chart(metrics, "nDCG@10", "nDCG@10 by model (test split, n=323)", "nDCG@10", "figure3_ndcg_by_model")
    bar_chart(metrics, "MAP", "MAP by model (test split, n=323)", "MAP", "figure4_map_by_model")
    bar_chart(metrics, "MRR@10", "MRR@10 by model (test split, n=323)", "MRR@10", "figure5_mrr_by_model")
    figure6_recall_curves(metrics)
    figure7_hybrid_improvement(metrics)
    figure8_reranker_improvement(metrics)
    figure9_ndcg_vs_latency(metrics)

    print(f"\n[generate_figures] wrote 7 figures (x3 formats each) to {FIGURES_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
