import pytest
from pydantic import ValidationError

from ip_copyright_inspector.schemas import CompareRequest, CompareResponse, LEGAL_NOTICE


def test_request_strips_outer_whitespace_and_uses_default_ngram_size() -> None:
    request = CompareRequest(left_text="  第一段  ", right_text="第二段")

    assert request.left_text == "第一段"
    assert request.ngram_size == 3


@pytest.mark.parametrize(
    "payload",
    [
        {"left_text": " ", "right_text": "有效"},
        {"left_text": "有效", "right_text": "\n\t"},
        {"left_text": "有效", "right_text": "有效", "ngram_size": 0},
        {"left_text": "有效", "right_text": "有效", "ngram_size": 9},
        {"left_text": "有效", "right_text": "有效", "unknown": True},
    ],
)
def test_request_rejects_invalid_or_extra_input(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        CompareRequest.model_validate(payload)


def test_response_always_carries_the_technical_notice() -> None:
    response = CompareResponse(
        record_id=1,
        score=0.5,
        ngram_size=2,
        left_ngram_count=3,
        right_ngram_count=3,
        intersection_count=2,
        union_count=4,
        left_normalized_length=4,
        right_normalized_length=4,
    )

    assert response.notice == LEGAL_NOTICE
    assert "不构成" in response.notice


def test_response_rejects_a_changed_notice() -> None:
    with pytest.raises(ValidationError):
        CompareResponse(
            record_id=1,
            score=0.5,
            ngram_size=2,
            left_ngram_count=3,
            right_ngram_count=3,
            intersection_count=2,
            union_count=4,
            left_normalized_length=4,
            right_normalized_length=4,
            notice="这是可修改的说明",
        )
