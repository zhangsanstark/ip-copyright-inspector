"""FastAPI application for the text-similarity exercise."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from .database import (
    ComparisonRecord,
    create_schema,
    dispose_engine,
    get_session,
)
from .schemas import CompareRequest, CompareResponse, HealthResponse
from .similarity import compare_texts


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await create_schema()
    try:
        yield
    finally:
        await dispose_engine()


app = FastAPI(
    title="IP Copyright Inspector",
    version="0.1.0",
    description=(
        "用于演示字符 n-gram Jaccard 相似度的技术筛查接口；"
        "输出不构成侵权或权属判断。"
    ),
    lifespan=lifespan,
)

SessionDependency = Annotated[AsyncSession, Depends(get_session)]


@app.exception_handler(RequestValidationError)
async def sanitized_validation_error(
    _: Request,
    error: RequestValidationError,
) -> JSONResponse:
    """Return validation details without echoing any submitted field value."""

    details: list[dict[str, Any]] = [
        {key: value for key, value in item.items() if key != "input"}
        for item in error.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=jsonable_encoder({"detail": details}),
    )


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    return HealthResponse()


@app.post(
    "/api/v1/comparisons",
    response_model=CompareResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["comparisons"],
)
async def create_comparison(
    request: CompareRequest,
    session: SessionDependency,
) -> CompareResponse:
    result = compare_texts(
        request.left_text,
        request.right_text,
        ngram_size=request.ngram_size,
    )
    record = ComparisonRecord(
        score=result.score,
        ngram_size=result.ngram_size,
        left_ngram_count=result.left_ngram_count,
        right_ngram_count=result.right_ngram_count,
        intersection_count=result.intersection_count,
        union_count=result.union_count,
        left_normalized_length=result.left_normalized_length,
        right_normalized_length=result.right_normalized_length,
    )
    session.add(record)

    try:
        await session.flush()
        record_id = record.id
        await session.commit()
    except SQLAlchemyError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="comparison result could not be persisted",
        ) from error

    return CompareResponse(
        record_id=record_id,
        score=result.score,
        ngram_size=result.ngram_size,
        left_ngram_count=result.left_ngram_count,
        right_ngram_count=result.right_ngram_count,
        intersection_count=result.intersection_count,
        union_count=result.union_count,
        left_normalized_length=result.left_normalized_length,
        right_normalized_length=result.right_normalized_length,
    )
