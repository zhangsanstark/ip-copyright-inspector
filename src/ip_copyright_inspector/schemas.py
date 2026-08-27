"""Pydantic v2 request and response contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

LEGAL_NOTICE = (
    "该分数仅表示字符片段集合的技术相似度，不构成侵权、权属或其他法律结论。"
)
LegalNotice = Literal[
    "该分数仅表示字符片段集合的技术相似度，不构成侵权、权属或其他法律结论。"
]


class CompareRequest(BaseModel):
    """Validated input for one text comparison."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    left_text: str = Field(
        min_length=1,
        max_length=100_000,
        description="待比较的第一段文本",
    )
    right_text: str = Field(
        min_length=1,
        max_length=100_000,
        description="待比较的第二段文本",
    )
    ngram_size: int = Field(
        default=3,
        ge=1,
        le=8,
        description="字符 n-gram 的 n，中文短文本可从 2 或 3 开始实验",
    )

    @field_validator("left_text", "right_text")
    @classmethod
    def reject_whitespace_only(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must contain at least one non-whitespace character")
        return value


class CompareResponse(BaseModel):
    """Stable public output contract for a comparison."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: int = Field(ge=1)
    method: Literal["character_ngram_jaccard"] = "character_ngram_jaccard"
    score: float = Field(ge=0.0, le=1.0)
    ngram_size: int = Field(ge=1, le=8)
    left_ngram_count: int = Field(ge=0)
    right_ngram_count: int = Field(ge=0)
    intersection_count: int = Field(ge=0)
    union_count: int = Field(ge=0)
    left_normalized_length: int = Field(ge=0)
    right_normalized_length: int = Field(ge=0)
    notice: LegalNotice = LEGAL_NOTICE


class HealthResponse(BaseModel):
    """Minimal liveness response."""

    model_config = ConfigDict(frozen=True)

    status: Literal["ok"] = "ok"
