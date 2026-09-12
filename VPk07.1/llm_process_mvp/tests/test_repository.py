"""Тесты SQLite-репозитория."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

import pytest

from src.domain.models import (
    Category,
    Confidence,
    LLMResult,
    Priority,
    ProcessingRecord,
    ProcessingStatus,
)
from src.infrastructure.repository import SQLiteProcessingRepository


def _record(raw: str) -> ProcessingRecord:
    return ProcessingRecord(
        id=None,
        created_at=datetime.now(timezone.utc),
        raw_input=raw,
        result=LLMResult(
            category=Category.OTHER,
            summary="ok",
            priority=Priority.LOW,
            next_action="none",
            fields={},
            confidence=Confidence.HIGH,
            escalate=False,
        ),
        status=ProcessingStatus.PROCESSED,
        error=None,
        model="fake",
    )


def test_save_and_get_roundtrip(repo) -> None:
    rid = repo.save(_record("hello"))
    fetched = repo.get(rid)
    assert fetched is not None
    assert fetched.raw_input == "hello"
    assert fetched.result is not None
    assert fetched.result.category == Category.OTHER


def test_list_recent_orders_desc(repo) -> None:
    first = repo.save(_record("first"))
    second = repo.save(_record("second"))
    rows = repo.list_recent(limit=10)
    assert [r.id for r in rows[:2]] == [second, first]


def test_connections_are_closed_after_use(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Регресс: каждое соединение должно быть закрыто после операции.

    Ранее использовался `with self._connect() as conn`, что является
    transaction context manager и НЕ закрывает соединение. На Windows это
    приводило к блокировке файла БД.
    """
    repo = SQLiteProcessingRepository(tmp_path / "leak.db")

    opened: list[sqlite3.Connection] = []
    original_connect = repo._connect

    def tracking_connect() -> sqlite3.Connection:
        conn = original_connect()
        opened.append(conn)
        return conn

    monkeypatch.setattr(repo, "_connect", tracking_connect)

    repo.save(_record("a"))
    repo.save(_record("b"))
    repo.list_recent(limit=10)

    assert len(opened) >= 3, "должны были открыться как минимум 3 соединения"
    for conn in opened:
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")