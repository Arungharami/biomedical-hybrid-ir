"""TF-IDF retrieval baseline (M1): scikit-learn ``TfidfVectorizer`` + cosine similarity.

Config: ``configs/tfidf.yaml -> tfidf`` (sublinear_tf, norm, smooth_idf,
use_idf, ngram_range, min_df, max_df) and ``-> lexical_preprocessing``
(delegated to :mod:`biomedical_ir.preprocessing` so TF-IDF and BM25 share the
exact same tokenization/normalization pipeline -- an apples-to-apples RQ1/H1
comparison).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .preprocessing import PreprocessConfig, preprocess_text


@dataclass
class TfidfConfig:
    sublinear_tf: bool = True
    norm: str = "l2"
    smooth_idf: bool = True
    use_idf: bool = True
    ngram_range: tuple[int, int] = (1, 1)
    min_df: int | float = 1
    max_df: int | float = 1.0
    top_k: int = 100

    @classmethod
    def from_config(cls, cfg: dict[str, Any]) -> TfidfConfig:
        t = cfg.get("tfidf", {})
        r = cfg.get("retrieval", {})
        ngram = t.get("ngram_range", [1, 1])
        return cls(
            sublinear_tf=t.get("sublinear_tf", True),
            norm=t.get("norm", "l2"),
            smooth_idf=t.get("smooth_idf", True),
            use_idf=t.get("use_idf", True),
            ngram_range=tuple(ngram),
            min_df=t.get("min_df", 1),
            max_df=t.get("max_df", 1.0),
            top_k=r.get("top_k", 100),
        )


class TfidfRetriever:
    """Fit once on a corpus, then rank documents for arbitrary queries.

    Preprocessing (unicode normalization, lowercasing, tokenization, optional
    stopword removal) is applied identically to documents and queries via a
    custom tokenizer function passed to ``TfidfVectorizer``, so sklearn's own
    lowercasing/token_pattern machinery is disabled in favor of
    :func:`biomedical_ir.preprocessing.preprocess_text`.
    """

    def __init__(
        self,
        tfidf_config: TfidfConfig | None = None,
        preprocess_config: PreprocessConfig | None = None,
    ):
        self.tfidf_config = tfidf_config or TfidfConfig()
        self.preprocess_config = preprocess_config or PreprocessConfig()
        self.vectorizer: TfidfVectorizer | None = None
        self.doc_ids: list[str] = []
        self.doc_matrix = None

    def _tokenizer(self, text: str) -> list[str]:
        return preprocess_text(text, self.preprocess_config)

    def _build_vectorizer(self) -> TfidfVectorizer:
        return TfidfVectorizer(
            tokenizer=self._tokenizer,
            preprocessor=lambda x: x,
            token_pattern=None,
            lowercase=False,  # handled inside preprocess_text, per config
            sublinear_tf=self.tfidf_config.sublinear_tf,
            norm=self.tfidf_config.norm,
            smooth_idf=self.tfidf_config.smooth_idf,
            use_idf=self.tfidf_config.use_idf,
            ngram_range=self.tfidf_config.ngram_range,
            min_df=self.tfidf_config.min_df,
            max_df=self.tfidf_config.max_df,
        )

    def fit(self, corpus: dict[str, str]) -> TfidfRetriever:
        """Fit the TF-IDF vectorizer over ``{doc_id: document_text}``."""
        self.doc_ids = list(corpus.keys())
        texts = [corpus[d] for d in self.doc_ids]
        self.vectorizer = self._build_vectorizer()
        self.doc_matrix = self.vectorizer.fit_transform(texts)
        return self

    def rank(self, query: str, top_k: int | None = None) -> list[tuple[str, float]]:
        """Rank all fitted documents against ``query``, returning the top ``top_k``."""
        if self.vectorizer is None or self.doc_matrix is None:
            raise RuntimeError("TfidfRetriever.fit() must be called before rank().")
        top_k = top_k if top_k is not None else self.tfidf_config.top_k
        q_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self.doc_matrix).ravel()
        return _top_k_ranked(self.doc_ids, scores, top_k)

    def rank_all(
        self, queries: dict[str, str], top_k: int | None = None
    ) -> dict[str, list[tuple[str, float]]]:
        """Rank every query in ``{query_id: query_text}``."""
        return {qid: self.rank(qtext, top_k) for qid, qtext in queries.items()}


def _top_k_ranked(doc_ids: list[str], scores: np.ndarray, top_k: int) -> list[tuple[str, float]]:
    k = min(top_k, len(doc_ids)) if top_k is not None else len(doc_ids)
    # Sort by descending score, tie-broken by ascending doc_id for determinism.
    order = sorted(range(len(doc_ids)), key=lambda i: (-scores[i], doc_ids[i]))[:k]
    return [(doc_ids[i], float(scores[i])) for i in order]


# ---------------------------------------------------------------------------
# Educational toy example (hand-computable), used by tests/test_tfidf.py.
# ---------------------------------------------------------------------------


def toy_corpus() -> dict[str, str]:
    """A tiny 3-document corpus with a hand-computable TF-IDF ground truth.

    Doc A: "cat dog cat"      (tokens: cat, dog, cat)
    Doc B: "dog bird"         (tokens: dog, bird)
    Doc C: "cat bird bird"    (tokens: cat, bird, bird)

    Vocabulary: {bird, cat, dog}. See ``tests/test_tfidf.py`` for the manual
    raw-TF / IDF / TF-IDF derivation this corpus supports.
    """
    return {
        "A": "cat dog cat",
        "B": "dog bird",
        "C": "cat bird bird",
    }
