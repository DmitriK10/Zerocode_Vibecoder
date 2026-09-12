"""Тесты доменных моделей и правил эскалации."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.domain.models import Confidence, LLMResult


def _valid_payload(**overrides):
    payload = {
        "category": "billing",
        "summary": "Клиент не получил счёт",
        "priority": "medium",
        "next_action": "Проверить биллинг",
        "fields": {"order_id": "42"},
        "confidence": "high",
        "escalate": False,
    }
    payload.update(overrides)
    return payload


def test_low_confidence_forces_escalation() -> None:
    """Правило: confidence=low всегда эскалирует."""
    result = LLMResult.model_validate(_valid_payload(confidence="low", escalate=False))
    assert result.confidence == Confidence.LOW
    assert result.escalate is True


def test_invalid_category_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        LLMResult.model_validate(_valid_payload(category="unknown_value"))


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        LLMResult.model_validate(_valid_payload(hallucinated_field="oops"))