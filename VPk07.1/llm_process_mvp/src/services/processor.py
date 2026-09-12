"""Оркестратор процесса: вход → LLM → валидация → эскалация → аудит → запись.

SRP: сервис знает только про протоколы LLMClient и ProcessingRepository.
"""
from __future__ import annotations

from datetime import datetime, timezone

from pydantic import ValidationError

from src.domain.models import (
    Category,
    Confidence,
    LLMResult,
    Priority,
    ProcessingRecord,
    ProcessingStatus,
)
from src.domain.protocols import LLMClient, ProcessingRepository


SAFE_FALLBACK: LLMResult = LLMResult(
    category=Category.OTHER,
    summary="Требуются уточнения. Обращение передано оператору.",
    priority=Priority.HIGH,
    next_action="Передать оператору/менеджеру для ручной обработки",
    fields={},
    confidence=Confidence.LOW,
    escalate=True,
)


class ProcessingService:
    """Основной сервис обработки входящего обращения."""

    def __init__(
        self,
        llm_client: LLMClient,
        repository: ProcessingRepository,
        model_name: str = "",
    ) -> None:
        self._llm = llm_client
        self._repo = repository
        self._model = model_name

    def process(self, raw_input: str) -> ProcessingRecord:
        """Обработать один вход и вернуть запись журнала."""
        if not raw_input or not raw_input.strip():
            return self._persist(
                raw_input=raw_input or "",
                result=SAFE_FALLBACK,
                status=ProcessingStatus.ESCALATED,
                error="Empty input",
            )

        # --- LLM вызов -----------------------------------------------------
        try:
            raw = self._llm.extract(raw_input)
        except Exception as exc:  # noqa: BLE001 — эскалируем любую ошибку LLM
            return self._persist(
                raw_input=raw_input,
                result=SAFE_FALLBACK,
                status=ProcessingStatus.ERROR,
                error=f"LLM call failed: {type(exc).__name__}: {exc}",
            )

        # --- Валидация схемы ----------------------------------------------
        try:
            result = LLMResult.model_validate(raw)
        except ValidationError as exc:
            return self._persist(
                raw_input=raw_input,
                result=SAFE_FALLBACK,
                status=ProcessingStatus.ESCALATED,
                error=f"JSON validation failed: {exc.errors()}",
            )

        # --- Финальный статус ---------------------------------------------
        status = (
            ProcessingStatus.ESCALATED
            if result.escalate
            else ProcessingStatus.PROCESSED
        )
        return self._persist(
            raw_input=raw_input,
            result=result,
            status=status,
            error=None,
        )

    def _persist(
        self,
        raw_input: str,
        result: LLMResult,
        status: ProcessingStatus,
        error: str | None,
    ) -> ProcessingRecord:
        record = ProcessingRecord(
            id=None,
            created_at=datetime.now(timezone.utc),
            raw_input=raw_input,
            result=result,
            status=status,
            error=error,
            model=self._model or None,
        )
        new_id = self._repo.save(record)
        return record.model_copy(update={"id": new_id})