"""Effectiveness/efficiency summary (M7, Section 19 of the project spec).

Pulls the timing/index fields each ``run_*.py`` script already recorded in
``results/metrics/*.json`` into one comparison table -- this module does not
re-measure anything itself (each script's own manifest/metrics timing is the
source of truth, captured at the moment that experiment actually ran).
"""

from __future__ import annotations

from typing import Any

# One row per model: which results/metrics/*.json field holds device/index
# info that isn't in every model's payload uniformly (TF-IDF/BM25 have no
# "device"/"index" block since they're pure-CPU, non-embedding methods).
_MODEL_FILES = {
    "tfidf": "tfidf.json",
    "bm25": "bm25.json",
    "bge": "bge.json",
    "medcpt": "medcpt.json",
    "hybrid_rrf": "hybrid_rrf.json",
    "hybrid_reranked": "hybrid_reranked.json",
}


def build_efficiency_table(metrics_dir) -> list[dict[str, Any]]:
    """Read every model's results/metrics/*.json and extract a common
    efficiency row: device, embedding_dim, index_size_bytes, latency."""
    import json
    from pathlib import Path

    metrics_dir = Path(metrics_dir)
    rows = []
    for model, filename in _MODEL_FILES.items():
        path = metrics_dir / filename
        if not path.exists():
            rows.append({"model": model, "status": "missing"})
            continue
        payload = json.loads(path.read_text())
        timing = payload.get("timing", {})
        index = payload.get("index", {})
        rows.append(
            {
                "model": model,
                "status": "complete",
                "device": payload.get("device", "cpu"),
                "embedding_dim": index.get("embedding_dim"),
                "index_size_bytes": index.get("size_bytes"),
                "latency_ms_per_query": timing.get("latency_ms_per_query"),
                "nDCG@10": payload.get("metrics", {}).get("nDCG@10"),
                "MAP": payload.get("metrics", {}).get("MAP"),
                "Recall@100": payload.get("metrics", {}).get("Recall@100"),
            }
        )
    return rows
