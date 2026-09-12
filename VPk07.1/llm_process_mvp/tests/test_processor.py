"""Тесты оркестратора ProcessingService (без сети)."""
from __future__ import annotations

from src.domain.models import ProcessingStatus
from src.services.processor import ProcessingService
from tests.conftest import FakeLLM


def _ok_payload():
    return {
        "category": "billing",
        "summary": "Клиент не получил счёт за март",
        "priority": "medium",
        "next_action": "Проверить статус счёта и ответить клиенту",
        "fields": {"order_id": "42"},
        "confidence": "high",
        "escalate": False,
    }


def test_happy_path_processed(repo) -> None:
    service = ProcessingService(FakeLLM(response=_ok_payload()), repo, model_name="fake")
    record = service.process("Не пришёл счёт за март, заказ 42")

    assert record.status == ProcessingStatus.PROCESSED
    assert record.result is not None
    assert record.result.escalate is False
    assert record.id is not None
    assert repo.get(record.id) is not None


def test_low_confidence_escalates(repo) -> None:
    payload = _ok_payload()
    payload["confidence"] = "low"
    payload["escalate"] = False  # сервис должен сам это поправить через модель
    service = ProcessingService(FakeLLM(response=payload), repo, model_name="fake")

    record = service.process("Что-то непонятное")
    assert record.status == ProcessingStatus.ESCALATED
    assert record.result is not None and record.result.escalate is True


def test_invalid_json_triggers_escalation_with_safe_result(repo) -> None:
    bad = {"unexpected": "structure"}
    service = ProcessingService(FakeLLM(response=bad), repo, model_name="fake")

    record = service.process("Какой-то текст")
    assert record.status == ProcessingStatus.ESCALATED
    assert record.error is not None and "validation failed" in record.error
    assert record.result is not None
    assert record.result.next_action.startswith("Передать оператору")


def test_llm_exception_is_recorded_as_error(repo) -> None:
    service = ProcessingService(
        FakeLLM(error=RuntimeError("proxy unavailable")), repo, model_name="fake"
    )
    record = service.process("Не могу оплатить")

    assert record.status == ProcessingStatus.ERROR
    assert "proxy unavailable" in (record.error or "")
    # безопасный fallback всё равно сохранён
    assert record.result is not None and record.result.escalate is True


def test_empty_input_is_escalated_without_llm_call(repo) -> None:
    fake = FakeLLM(response=_ok_payload())
    service = ProcessingService(fake, repo, model_name="fake")

    record = service.process("   ")
    assert record.status == ProcessingStatus.ESCALATED
    assert fake.calls == 0