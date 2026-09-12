"""SQLite-репозиторий журнала аудита.

Реализует порт ProcessingRepository.

Про управление соединениями:
    `with sqlite3.connect(...)` в Python — это transaction context manager,
    НЕ resource context manager. Он коммитит/откатывает транзакцию, но НЕ
    закрывает соединение. Здесь каждое соединение оборачивается в
    `contextlib.closing`, чтобы file handles освобождались сразу.
    На Windows без этого файл processing.db блокируется на всё время
    работы процесса.
"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.domain.models import LLMResult, ProcessingRecord, ProcessingStatus


SCHEMA_SQL: str = """
CREATE TABLE IF NOT EXISTS processing_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at   TEXT    NOT NULL,
    raw_input    TEXT    NOT NULL,
    result_json  TEXT,
    status       TEXT    NOT NULL,
    error        TEXT,
    model        TEXT
);
CREATE INDEX IF NOT EXISTS idx_processing_log_created_at
    ON processing_log (created_at DESC);
"""


class SQLiteProcessingRepository:
    """Репозиторий журнала обработки на SQLite."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # --- Порт -------------------------------------------------------------
    def save(self, record: ProcessingRecord) -> int:
        with closing(self._connect()) as conn:
            cur = conn.execute(
                "INSERT INTO processing_log "
                "(created_at, raw_input, result_json, status, error, model) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    record.created_at.isoformat(),
                    record.raw_input,
                    record.result.model_dump_json() if record.result else None,
                    record.status.value,
                    record.error,
                    record.model,
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def get(self, record_id: int) -> Optional[ProcessingRecord]:
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT * FROM processing_log WHERE id = ?", (record_id,)
            ).fetchone()
        return self._row_to_record(row) if row else None

    def list_recent(self, limit: int = 50) -> List[ProcessingRecord]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM processing_log ORDER BY id DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
        return [self._row_to_record(r) for r in rows]

    # --- Internals --------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with closing(self._connect()) as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> ProcessingRecord:
        result: Optional[LLMResult] = (
            LLMResult.model_validate_json(row["result_json"])
            if row["result_json"]
            else None
        )
        return ProcessingRecord(
            id=int(row["id"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            raw_input=row["raw_input"],
            result=result,
            status=ProcessingStatus(row["status"]),
            error=row["error"],
            model=row["model"],
        )