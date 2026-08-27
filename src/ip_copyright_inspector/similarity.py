"""Deterministic character n-gram similarity helpers."""

from __future__ import annotations

from dataclasses import dataclass
import unicodedata

MIN_NGRAM_SIZE = 1
MAX_NGRAM_SIZE = 8


@dataclass(frozen=True, slots=True)
class SimilarityResult:
    """The auditable intermediate values of one Jaccard comparison."""

    score: float
    ngram_size: int
    left_ngram_count: int
    right_ngram_count: int
    intersection_count: int
    union_count: int
    left_normalized_length: int
    right_normalized_length: int


def normalize_text(text: str) -> str:
    """Normalize width and case, then remove Unicode whitespace.

    Punctuation is intentionally preserved. This makes the transformation easy
    to explain and avoids silently performing language-specific tokenization.
    """

    normalized = unicodedata.normalize("NFKC", text).casefold()
    return "".join(character for character in normalized if not character.isspace())


def character_ngrams(text: str, ngram_size: int) -> set[str]:
    """Return the unique character n-grams of normalized input text.

    A non-empty text shorter than ``ngram_size`` becomes one fallback token
    containing the whole normalized text. Without that rule, every short text
    would produce an empty set and unrelated short texts could look identical.
    Empty normalized text still produces an empty set.
    """

    if not MIN_NGRAM_SIZE <= ngram_size <= MAX_NGRAM_SIZE:
        raise ValueError(
            f"ngram_size must be between {MIN_NGRAM_SIZE} and {MAX_NGRAM_SIZE}"
        )

    normalized = normalize_text(text)
    if not normalized:
        return set()
    if len(normalized) < ngram_size:
        return {normalized}

    stop = len(normalized) - ngram_size + 1
    return {normalized[index : index + ngram_size] for index in range(stop)}


def compare_texts(
    left_text: str,
    right_text: str,
    *,
    ngram_size: int = 3,
) -> SimilarityResult:
    """Compare two texts with Jaccard similarity over character n-gram sets.

    Two empty normalized inputs are treated as identical and receive 1.0. The
    API schema rejects blank text, but the library function keeps this edge case
    explicit for callers that use it directly.
    """

    left_normalized = normalize_text(left_text)
    right_normalized = normalize_text(right_text)
    left_ngrams = character_ngrams(left_text, ngram_size)
    right_ngrams = character_ngrams(right_text, ngram_size)
    intersection_count = len(left_ngrams & right_ngrams)
    union_count = len(left_ngrams | right_ngrams)
    score = intersection_count / union_count if union_count else 1.0

    return SimilarityResult(
        score=score,
        ngram_size=ngram_size,
        left_ngram_count=len(left_ngrams),
        right_ngram_count=len(right_ngrams),
        intersection_count=intersection_count,
        union_count=union_count,
        left_normalized_length=len(left_normalized),
        right_normalized_length=len(right_normalized),
    )
