"""Lexical preprocessing for the TF-IDF / BM25 pipeline (Section 6 of the spec).

Configurable per ``configs/tfidf.yaml`` / ``configs/bm25.yaml`` ->
``lexical_preprocessing``:

    unicode_normalize: "NFKC" | "NFC" | "NFD" | "NFKD" | null
    lowercase: bool
    strip_punctuation: bool   # meaningful for the "whitespace" tokenizer;
                               # the "regex" (\\w+) tokenizer never emits
                               # punctuation tokens in the first place, so
                               # this is a no-op there by construction
    remove_stopwords: bool    # OFF by default in both configs -- do not
                               # silently drop biomedical terms. Only used
                               # when explicitly enabled, and only with the
                               # small generic-English list below (no
                               # biomedical-aware trimming is ever applied)
    tokenizer: "regex" | "whitespace"
    min_token_len: int

Both TF-IDF (``tfidf.py``) and BM25 (``bm25.py``) call
:func:`preprocess_text` so the two classical baselines are compared on an
identical lexical pipeline (an apples-to-apples RQ1/H1 comparison).

Contract with the transformer pipeline (M3+, BGE/MedCPT/cross-encoder):
those models consume **raw, unpreprocessed text** through their own
model-specific subword tokenizer (WordPiece/BPE) -- no lowercasing,
stopword removal, or stemming is applied beforehand. Subword tokenizers
already handle casing and morphology internally, and stripping "stopwords"
before a transformer's attention mechanism sees them would destroy
meaning-bearing function words the model was pretrained to use. This
module's functions are used ONLY for the lexical (TF-IDF/BM25) baselines;
``dense.py`` / ``medcpt.py`` (M3/M4) must not call into it.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

_REGEX_TOKEN = re.compile(r"\w+", re.UNICODE)

# A small, generic English stopword list -- intentionally NOT biomedical-
# aware, and only ever consulted when remove_stopwords=True is explicitly
# set (both configs/tfidf.yaml and configs/bm25.yaml default this to False).
DEFAULT_STOPWORDS: frozenset[str] = frozenset(
    {
        "a", "an", "the", "and", "or", "but", "if", "of", "to", "in", "on",
        "for", "with", "is", "are", "was", "were", "be", "been", "being",
        "this", "that", "these", "those", "it", "its", "as", "at", "by",
        "from", "into", "than", "then", "so", "such", "not", "no", "nor",
        "do", "does", "did", "has", "have", "had", "can", "could", "will",
        "would", "should", "may", "might", "must", "shall", "i", "you",
        "he", "she", "we", "they", "them", "his", "her", "their", "our",
        "your", "also",
    }
)


@dataclass
class PreprocessConfig:
    unicode_normalize: str | None = "NFKC"
    lowercase: bool = True
    strip_punctuation: bool = True
    remove_stopwords: bool = False
    tokenizer: str = "regex"
    min_token_len: int = 1
    stopwords: frozenset[str] = field(default_factory=lambda: DEFAULT_STOPWORDS)

    @classmethod
    def from_config(cls, cfg: dict) -> PreprocessConfig:
        """Build from a loaded config dict (either the full config, containing a
        ``lexical_preprocessing`` key, or that sub-block directly)."""
        block = cfg.get("lexical_preprocessing", cfg) if isinstance(cfg, dict) else {}
        return cls(
            unicode_normalize=block.get("unicode_normalize", "NFKC"),
            lowercase=block.get("lowercase", True),
            strip_punctuation=block.get("strip_punctuation", True),
            remove_stopwords=block.get("remove_stopwords", False),
            tokenizer=block.get("tokenizer", "regex"),
            min_token_len=block.get("min_token_len", 1),
        )


def normalize_text(text: str, form: str | None = "NFKC") -> str:
    """Unicode-normalize ``text``. ``form`` of ``None`` is a no-op."""
    if not form:
        return text
    return unicodedata.normalize(form, text)


def tokenize(text: str, tokenizer: str = "regex") -> list[str]:
    """Split ``text`` into tokens.

    ``"regex"`` uses ``\\w+`` (word characters -- letters, digits,
    underscore -- across any language, per Python's ``re.UNICODE``
    default), which naturally drops punctuation and whitespace.
    ``"whitespace"`` is a plain ``str.split()`` and preserves any attached
    punctuation, so it is meant to be paired with ``strip_punctuation=True``.
    """
    if tokenizer == "regex":
        return _REGEX_TOKEN.findall(text)
    if tokenizer == "whitespace":
        return text.split()
    raise ValueError(f"Unknown tokenizer: {tokenizer!r}")


def preprocess_text(text: str, config: PreprocessConfig | None = None) -> list[str]:
    """Run the full configurable lexical pipeline and return a token list."""
    config = config or PreprocessConfig()
    if not text:
        return []
    text = normalize_text(text, config.unicode_normalize)
    if config.lowercase:
        text = text.lower()
    tokens = tokenize(text, config.tokenizer)
    if config.strip_punctuation and config.tokenizer == "whitespace":
        tokens = [re.sub(r"[^\w]", "", t) for t in tokens]
        tokens = [t for t in tokens if t]
    if config.remove_stopwords:
        tokens = [t for t in tokens if t not in config.stopwords]
    if config.min_token_len > 1:
        tokens = [t for t in tokens if len(t) >= config.min_token_len]
    return tokens


def preprocess_to_string(text: str, config: PreprocessConfig | None = None) -> str:
    """Convenience wrapper: space-joined preprocessed tokens."""
    return " ".join(preprocess_text(text, config))
