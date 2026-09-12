"""Общие фикстуры для тестов.

Помимо фикстур здесь решается задача импорта top-level скриптов
(smoke_test.py, run_batch.py), которые не являются частью пакета `src`.

Почему sys.path.insert, а не `pythonpath` в pyproject.toml:
    pytest подхватывает pythonpath только если найден соответствующий
    pyproject.toml (или pytest.ini). Но конфиг легко перебивается другим
    ini-файлом, или pytest может запускаться не из корня. conftest.py
    же загружается всегда и до импорта тестов, поэтому мы гарантированно
    кладём корень проекта в sys.path. Это идиоматично и предсказуемо.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pytest


# --- Гарантируем импортируемость top-level скриптов -----------------------
# conftest.py находится в <project>\tests\conftest.py
# parents[0] = <project>\tests
# parents[1] = <project>
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


from src.infrastructure.repository import SQLiteProcessingRepository  # noqa: E402


class FakeLLM:
    """Тестовый LLM-клиент: либо возвращает заранее заданный dict, либо падает."""

    def __init__(
        self,
        response: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ) -> None:
        self._response = response
        self._error = error
        self.calls: int = 0

    def extract(self, text: str) -> Dict[str, Any]:
        self.calls += 1
        if self._error is not None:
            raise self._error
        return dict(self._response or {})


@pytest.fixture()
def repo(tmp_path: Path) -> SQLiteProcessingRepository:
    """Изолированный SQLite-репозиторий в tmp_path."""
    return SQLiteProcessingRepository(tmp_path / "test.db")