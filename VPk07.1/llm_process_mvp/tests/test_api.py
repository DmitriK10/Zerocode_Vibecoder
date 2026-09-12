"""Интеграционные тесты FastAPI с подменой зависимостей."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src.api.app import app, get_repository, get_service
from src.domain.models import (
    Category,
    Confidence,
    LLMResult,
    Priority,
    ProcessingRecord,
    ProcessingStatus,
)
from src.services.processor import ProcessingService
from tests.conftest import FakeLLM


def _payload() -> dict:
    return {
        "category": "technical",
        "summary": "Сайт не работает",
        "priority": "high",
        "next_action": "Проверить доступность",
        "fields": {},
        "confidence": "high",
        "escalate": False,
    }


def _override(repo, llm) -> object:
    return lambda: ProcessingService(llm, repo, model_name="fake")


def test_ingest_happy_path(repo) -> None:
    app.dependency_overrides[get_service] = _override(repo, FakeLLM(response=_payload()))
    try:
        client = TestClient(app)
        resp = client.post("/ingest", json={"text": "Сайт упал!"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "processed"
        assert data["escalate"] is False
        assert data["result"]["category"] == "technical"
        # Запись должна реально попасть в репозиторий
        assert repo.get(data["id"]) is not None
    finally:
        app.dependency_overrides.clear()


def test_ingest_validation_error_on_empty_text(repo) -> None:
    app.dependency_overrides[get_service] = _override(repo, FakeLLM(response=_payload()))
    try:
        client = TestClient(app)
        resp = client.post("/ingest", json={"text": ""})
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_log_endpoint_returns_records(repo) -> None:
    """GET /log читает из репозитория, не завися от LLM."""
    app.dependency_overrides[get_repository] = lambda: repo
    try:
        repo.save(
            ProcessingRecord(
                id=None,
                created_at=datetime.now(timezone.utc),
                raw_input="test",
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
        )

        client = TestClient(app)
        resp = client.get("/log?limit=5")
        assert resp.status_code == 200
        records = resp.json()
        assert isinstance(records, list)
        assert len(records) == 1
        assert records[0]["raw_input"] == "test"
    finally:
        app.dependency_overrides.clear()


def test_log_endpoint_does_not_require_llm() -> None:
    """Регресс: /log не должен зависеть от get_service (LLM).

    Ранее в сигнатуре был `service: ProcessingService = Depends(get_service)`,
    что заставляло FastAPI строить LLM-клиент для чтения журнала.
    """
    import inspect

    from src.api import app as app_module

    sig = inspect.signature(app_module.read_log)
    param_names = set(sig.parameters.keys())
    assert "service" not in param_names, (
        "/log не должен зависеть от ProcessingService — только от репозитория"
    )
    assert "repo" in param_names