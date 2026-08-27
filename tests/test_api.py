from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from pathlib import Path
import sqlite3
from typing import Any, Literal

import pytest

pytest.importorskip(
    "httpx2",
    reason="FastAPI TestClient requires the optional httpx2 test dependency",
)

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ip_copyright_inspector import database
from ip_copyright_inspector.database import ComparisonRecord, get_session
from ip_copyright_inspector.main import app
from ip_copyright_inspector.schemas import LEGAL_NOTICE


@pytest.fixture
def api_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, Path]]:
    """Run the application against a fresh SQLite file for every test."""

    database_path = tmp_path / "api-test.db"
    test_engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "async_session_factory", test_session_factory)
    app.dependency_overrides.clear()

    with TestClient(app) as client:
        yield client, database_path

    app.dependency_overrides.clear()


def comparison_payload() -> dict[str, object]:
    return {
        "left_text": "红色披风与星形徽章",
        "right_text": "星形徽章搭配红色披风",
        "ngram_size": 2,
    }


def test_health(api_client: tuple[TestClient, Path]) -> None:
    client, _ = api_client

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_returns_201_fixed_notice_and_persists_metadata(
    api_client: tuple[TestClient, Path],
) -> None:
    client, database_path = api_client

    response = client.post("/api/v1/comparisons", json=comparison_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["record_id"] >= 1
    assert body["notice"] == LEGAL_NOTICE
    assert body["method"] == "character_ngram_jaccard"
    assert 0.0 <= body["score"] <= 1.0

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM comparison_records WHERE id = ?",
            (body["record_id"],),
        ).fetchone()

    assert row is not None
    assert row["method"] == body["method"]
    assert row["score"] == pytest.approx(body["score"])
    assert row["ngram_size"] == body["ngram_size"]
    assert row["intersection_count"] == body["intersection_count"]
    assert row["union_count"] == body["union_count"]
    assert "left_text" not in row.keys()
    assert "right_text" not in row.keys()


def test_validation_response_does_not_echo_sensitive_input(
    api_client: tuple[TestClient, Path],
) -> None:
    client, _ = api_client
    sensitive_marker = "private-original-marker-7f5f3a"
    oversized_text = sensitive_marker + ("x" * 100_000)
    payload = comparison_payload() | {"left_text": oversized_text}

    response = client.post("/api/v1/comparisons", json=payload)

    assert response.status_code == 422
    assert sensitive_marker not in response.text
    details = response.json()["detail"]
    assert details
    assert all("input" not in item for item in details)


class FailingSession:
    """Small session double used to prove both failure paths roll back."""

    def __init__(self, failure_stage: Literal["flush", "commit"]) -> None:
        self.failure_stage = failure_stage
        self.record: ComparisonRecord | None = None
        self.flush_called = False
        self.commit_called = False
        self.rollback_called = False

    def add(self, record: ComparisonRecord) -> None:
        self.record = record

    async def flush(self) -> None:
        self.flush_called = True
        if self.failure_stage == "flush":
            raise SQLAlchemyError("forced flush failure")
        if self.record is None:
            raise AssertionError("record must be added before flush")
        self.record.id = 101

    async def commit(self) -> None:
        self.commit_called = True
        if self.failure_stage == "commit":
            raise SQLAlchemyError("forced commit failure")

    async def rollback(self) -> None:
        self.rollback_called = True


@pytest.mark.parametrize("failure_stage", ["flush", "commit"])
def test_persistence_failure_rolls_back_and_returns_503(
    api_client: tuple[TestClient, Path],
    failure_stage: Literal["flush", "commit"],
) -> None:
    client, _ = api_client
    failing_session = FailingSession(failure_stage)

    async def override_session() -> AsyncIterator[Any]:
        yield failing_session

    app.dependency_overrides[get_session] = override_session
    try:
        response = client.post("/api/v1/comparisons", json=comparison_payload())
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 503
    assert response.json() == {
        "detail": "comparison result could not be persisted"
    }
    assert failing_session.flush_called is True
    assert failing_session.rollback_called is True
    assert failing_session.commit_called is (failure_stage == "commit")
