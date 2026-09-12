"""Абстракции (порты) для соблюдения DIP.

Сервисный слой зависит только от этих протоколов, а не от конкретных
реализаций OpenAI/SQLite.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from src.domain.models import ProcessingRecord


@runtime_checkable
class LLMClient(Protocol):
    """Порт LLM-клиента: текст → сырой dict (ещё не провалидированный)."""

    def extract(self, text: str) -> Dict[str, Any]:
        ...


@runtime_checkable
class ProcessingRepository(Protocol):
    """Порт журнала аудита."""

    def save(self, record: ProcessingRecord) -> int:
        ...

    def get(self, record_id: int) -> Optional[ProcessingRecord]:
        ...

    def list_recent(self, limit: int = 50) -> List[ProcessingRecord]:
        ...