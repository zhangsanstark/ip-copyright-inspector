import pytest

from ip_copyright_inspector.similarity import (
    character_ngrams,
    compare_texts,
    normalize_text,
)


def test_normalize_text_handles_width_case_and_whitespace() -> None:
    assert normalize_text(" Ａ B\tC\n") == "abc"


def test_character_ngrams_are_unique() -> None:
    assert character_ngrams("aaaa", 2) == {"aa"}


def test_short_non_empty_text_becomes_one_fallback_token() -> None:
    assert character_ngrams(" A ", 3) == {"a"}
    assert character_ngrams("", 3) == set()


def test_different_short_texts_do_not_collapse_to_two_empty_sets() -> None:
    result = compare_texts("甲", "乙", ngram_size=3)

    assert result.score == 0.0
    assert result.left_ngram_count == 1
    assert result.right_ngram_count == 1
    assert result.union_count == 2


def test_jaccard_score_has_auditable_counts() -> None:
    result = compare_texts("abcd", "abce", ngram_size=2)

    assert result.score == pytest.approx(0.5)
    assert result.left_ngram_count == 3
    assert result.right_ngram_count == 3
    assert result.intersection_count == 2
    assert result.union_count == 4


def test_chinese_text_ignores_spacing_but_preserves_content() -> None:
    result = compare_texts("知识 产权保护", "知识产权保护", ngram_size=2)

    assert result.score == 1.0


@pytest.mark.parametrize(
    ("left_text", "right_text", "expected"),
    [
        ("", "", 1.0),
        ("", "内容", 0.0),
        ("ab", "ab", 1.0),
        ("Python", "PYTHON", 1.0),
    ],
)
def test_edge_cases_are_explicit(
    left_text: str,
    right_text: str,
    expected: float,
) -> None:
    assert compare_texts(left_text, right_text, ngram_size=3).score == expected


@pytest.mark.parametrize("ngram_size", [0, 9])
def test_invalid_ngram_size_is_rejected(ngram_size: int) -> None:
    with pytest.raises(ValueError, match="ngram_size"):
        character_ngrams("text", ngram_size)
