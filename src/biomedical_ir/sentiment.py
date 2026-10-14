"""Patient-review extension: rating-derived labels, separate from IR qrels."""

from __future__ import annotations

import hashlib
import html
import math

LABELS = ["negative", "neutral", "positive"]


def clean_review(text: str) -> str:
    return " ".join(html.unescape(text).split())


def text_hash(text: str) -> str:
    return hashlib.sha256(clean_review(text).casefold().encode()).hexdigest()


def rating_label(rating: float) -> str:
    rating = float(rating)
    if not math.isfinite(rating) or not 1 <= rating <= 10:
        raise ValueError("Rating must be finite and between 1 and 10")
    return "negative" if rating <= 4 else "neutral" if rating <= 6 else "positive"


def prepare_reviews(rows, excluded_hashes=()):
    """Keep one normalized review, exclude earlier partitions, audit removals."""
    seen = set(excluded_hashes)
    records = []
    audit = {"input": 0, "invalid": 0, "duplicate_or_overlap": 0, "kept": 0}
    for row in rows:
        audit["input"] += 1
        try:
            text = clean_review(row["review"])
            label = rating_label(row["rating"])
            if not text:
                raise ValueError("Empty review")
        except (KeyError, TypeError, ValueError):
            audit["invalid"] += 1
            continue
        key = text_hash(text)
        if key in seen:
            audit["duplicate_or_overlap"] += 1
            continue
        seen.add(key)
        records.append({"text": text, "label": label, "hash": key})
    audit["kept"] = len(records)
    return records, audit
