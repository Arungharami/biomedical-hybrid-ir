"""Transparent from-scratch Okapi BM25 (M2).

This is a project implementation (not a wrapper around ``rank_bm25`` or any
other library) so term-saturation and length-normalization behavior are
directly inspectable -- Section 6 of the project spec explicitly allows "a
transparent project implementation" in place of a third-party black box.

IDF formula -- there are a few conventions in the literature, so the exact
one used here is stated precisely: the classical Robertson/Sparck-Jones IDF
with +0.5 smoothing, as given in Robertson & Zaragoza (2009), "The
Probabilistic Relevance Framework: BM25 and Beyond":

    idf(t) = log( (N - n(t) + 0.5) / (n(t) + 0.5) )

where ``N`` is the number of documents in the corpus and ``n(t)`` is the
number of documents containing term ``t``. NOTE: unlike some practical
re-derivations (e.g. Lucene's ``BM25Similarity``, which adds +1 inside the
log to force non-negativity), this formula does **not** add +1, so idf(t)
can go slightly negative for terms occurring in more than half the corpus.
This is a known, documented property of the classical formula -- rare for
genuine content terms, and not clipped here, to stay transparent about what
the textbook formula actually produces rather than silently patching it.

Per-term score contribution of term ``t`` to document ``D`` given query ``Q``:

    score(D, t) = idf(t) * f(t, D) * (k1 + 1)
                  ------------------------------------------------
                  f(t, D) + k1 * (1 - b + b * |D| / avgdl)

``f(t, D)`` is the raw term frequency of ``t`` in ``D``, ``|D|`` is the
document's token length, and ``avgdl`` is the corpus's average document
length. ``score(D, Q) = sum`` over query terms ``t`` of ``score(D, t)``
(terms absent from ``D`` contribute 0).

``k1`` (term-frequency saturation) and ``b`` (length-normalization
strength) default to 1.2 / 0.75 per ``configs/bm25.yaml``, the suggested
initial values from Robertson & Zaragoza (2009). ``configs/bm25.yaml`` has
``tuning.enabled: false`` for this milestone, so these defaults are used
frozen, with no dev-split grid search performed.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from .preprocessing import PreprocessConfig, preprocess_text


@dataclass
class BM25Config:
    k1: float = 1.2
    b: float = 0.75
    top_k: int = 100

    @classmethod
    def from_config(cls, cfg: dict[str, Any]) -> BM25Config:
        bm = cfg.get("bm25", {})
        r = cfg.get("retrieval", {})
        return cls(k1=bm.get("k1", 1.2), b=bm.get("b", 0.75), top_k=r.get("top_k", 100))


class BM25Retriever:
    """Fit once on a corpus (builds an inverted index + document-length stats),
    then rank documents for arbitrary queries. Mirrors :class:`biomedical_ir.tfidf.TfidfRetriever`'s
    ``fit`` / ``rank`` / ``rank_all`` interface so both baselines can be evaluated identically.
    """

    def __init__(
        self,
        bm25_config: BM25Config | None = None,
        preprocess_config: PreprocessConfig | None = None,
    ):
        self.config = bm25_config or BM25Config()
        self.preprocess_config = preprocess_config or PreprocessConfig()
        self.doc_ids: list[str] = []
        self.doc_freqs: dict[str, int] = {}
        self.doc_term_counts: dict[str, Counter] = {}
        self.doc_len: dict[str, int] = {}
        self.avgdl: float = 0.0
        self.N: int = 0
        self._postings: dict[str, set[str]] = defaultdict(set)
        self._idf_cache: dict[str, float] = {}

    def fit(self, corpus: dict[str, str]) -> BM25Retriever:
        """Index ``{doc_id: document_text}``: tokenize, build postings, compute IDF."""
        self.doc_ids = list(corpus.keys())
        self.N = len(self.doc_ids)
        total_len = 0
        for doc_id, text in corpus.items():
            tokens = preprocess_text(text, self.preprocess_config)
            counts = Counter(tokens)
            self.doc_term_counts[doc_id] = counts
            self.doc_len[doc_id] = len(tokens)
            total_len += len(tokens)
            for term in counts:
                self._postings[term].add(doc_id)
        self.avgdl = total_len / self.N if self.N else 0.0
        self.doc_freqs = {t: len(ds) for t, ds in self._postings.items()}
        self._idf_cache = {t: self._idf(df) for t, df in self.doc_freqs.items()}
        return self

    def _idf(self, doc_freq: int) -> float:
        return math.log((self.N - doc_freq + 0.5) / (doc_freq + 0.5))

    def score(self, query_tokens: list[str], doc_id: str) -> float:
        """BM25 score of a single document against an already-tokenized query."""
        k1, b = self.config.k1, self.config.b
        dl = self.doc_len.get(doc_id, 0)
        counts = self.doc_term_counts.get(doc_id, {})
        norm_factor = k1 * (1 - b + b * dl / self.avgdl) if self.avgdl else 0.0
        total = 0.0
        for term in query_tokens:
            tf = counts.get(term, 0)
            if tf == 0:
                continue
            idf = self._idf_cache.get(term)
            if idf is None:
                continue  # term never seen anywhere in the fitted corpus
            total += idf * tf * (k1 + 1) / (tf + norm_factor)
        return total

    def rank(self, query: str, top_k: int | None = None) -> list[tuple[str, float]]:
        """Rank documents against ``query``, returning the top ``top_k`` by BM25 score.

        Only documents sharing at least one query term are scored/returned
        (documents with zero term overlap have BM25 score 0 by construction
        and are excluded, matching standard inverted-index retrieval
        practice rather than returning the entire corpus at score 0).
        """
        if not self.doc_ids:
            raise RuntimeError("BM25Retriever.fit() must be called before rank().")
        top_k = top_k if top_k is not None else self.config.top_k
        query_tokens = preprocess_text(query, self.preprocess_config)
        candidates: set[str] = set()
        for t in query_tokens:
            candidates |= self._postings.get(t, set())
        if not candidates:
            return []
        scored = [(d, self.score(query_tokens, d)) for d in candidates]
        scored.sort(key=lambda x: (-x[1], x[0]))
        k = min(top_k, len(scored)) if top_k is not None else len(scored)
        return scored[:k]

    def rank_all(
        self, queries: dict[str, str], top_k: int | None = None
    ) -> dict[str, list[tuple[str, float]]]:
        """Rank every query in ``{query_id: query_text}``."""
        return {qid: self.rank(qtext, top_k) for qid, qtext in queries.items()}


# ---------------------------------------------------------------------------
# Educational toy example (hand-computable), used by tests/test_bm25.py.
# ---------------------------------------------------------------------------


def toy_corpus() -> dict[str, str]:
    """A tiny 3-document corpus with a hand-computable BM25 ground truth.

    Doc A: "cat dog cat"      (length 3)
    Doc B: "dog bird"         (length 2)
    Doc C: "cat bird bird"    (length 3)

    Shared with :func:`biomedical_ir.tfidf.toy_corpus` (identical documents)
    so TF-IDF and BM25 can be compared side by side on the same toy example.
    """
    return {
        "A": "cat dog cat",
        "B": "dog bird",
        "C": "cat bird bird",
    }
