"""Tests for :mod:`app.llm.parser`.

Covers schema validation, quote verification and business quality rules.
"""

from __future__ import annotations

import json

import pytest

from app.domain.enums import Priority, ReviewSeverity
from app.llm.exceptions import LLMParseError
from app.llm.parser import (
    CRITICAL_CONFIDENCE_THRESHOLD,
    parse_llm_response,
)

SOURCE_TEXT = (
    "Иван, привет! Нужно до пятницы подготовить отчёт по продажам. "
    "Также свяжись с Марией по поводу логотипа. Не забудь про налоги."
)


def _make_item(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "title": "Подготовить отчёт",
        "assignee": "Иван",
        "due_date_raw": "до пятницы",
        "due_date_iso": "2026-09-19",
        "priority": "high",
        "source_quote": "Нужно до пятницы подготовить отчёт по продажам",
        "confidence": 0.92,
        "needs_review": False,
        "review_reason": None,
        "review_severity": None,
    }
    base.update(overrides)
    return base


def _json(*items: dict[str, object]) -> str:
    return json.dumps({"actions": list(items)})


# ----------------------------------------------------------------- schema


def test_valid_payload_produces_action_create() -> None:
    result = parse_llm_response(_json(_make_item()), SOURCE_TEXT)
    assert len(result) == 1
    item = result[0]
    assert item.title == "Подготовить отчёт"
    assert item.priority is Priority.HIGH
    assert item.needs_review is False
    assert item.review_severity is None
    assert item.confidence == pytest.approx(0.92)


def test_malformed_json_raises_parse_error() -> None:
    with pytest.raises(LLMParseError):
        parse_llm_response("not-a-json", SOURCE_TEXT)


def test_extra_field_raises_parse_error() -> None:
    payload = _json(_make_item(unexpected_field="boom"))
    with pytest.raises(LLMParseError):
        parse_llm_response(payload, SOURCE_TEXT)


def test_missing_required_field_raises_parse_error() -> None:
    payload = _json(
        {
            "title": "No priority",
            "source_quote": "Нужно до пятницы",
            "confidence": 0.9,
            "needs_review": False,
            "review_reason": None,
            "review_severity": None,
        }
    )
    with pytest.raises(LLMParseError):
        parse_llm_response(payload, SOURCE_TEXT)


def test_invalid_priority_raises_parse_error() -> None:
    payload = _json(_make_item(priority="urgent"))
    with pytest.raises(LLMParseError):
        parse_llm_response(payload, SOURCE_TEXT)


def test_confidence_out_of_range_raises_parse_error() -> None:
    payload = _json(_make_item(confidence=1.5))
    with pytest.raises(LLMParseError):
        parse_llm_response(payload, SOURCE_TEXT)


def test_needs_review_true_requires_reason() -> None:
    payload = _json(
        _make_item(needs_review=True, review_reason=None, review_severity="critical")
    )
    with pytest.raises(LLMParseError):
        parse_llm_response(payload, SOURCE_TEXT)


def test_severity_without_needs_review_rejected() -> None:
    payload = _json(
        _make_item(needs_review=False, review_reason=None, review_severity="soft")
    )
    with pytest.raises(LLMParseError):
        parse_llm_response(payload, SOURCE_TEXT)


# ------------------------------------------------------------- quality rules


def test_hallucinated_quote_forces_critical_review() -> None:
    payload = _json(
        _make_item(
            source_quote="Уволить всех сотрудников отдела маркетинга",
            confidence=0.95,
            needs_review=False,
            review_reason=None,
            review_severity=None,
        )
    )
    (item,) = parse_llm_response(payload, SOURCE_TEXT)
    assert item.needs_review is True
    assert item.review_severity is ReviewSeverity.CRITICAL
    assert item.review_reason is not None
    assert "Цитата" in item.review_reason


def test_low_confidence_forces_critical_review() -> None:
    payload = _json(
        _make_item(
            confidence=CRITICAL_CONFIDENCE_THRESHOLD - 0.05,
            needs_review=False,
            review_reason=None,
            review_severity=None,
        )
    )
    (item,) = parse_llm_response(payload, SOURCE_TEXT)
    assert item.needs_review is True
    assert item.review_severity is ReviewSeverity.CRITICAL
    assert item.review_reason is not None
    assert "уверенность" in item.review_reason


def test_missing_assignee_marks_soft_review() -> None:
    payload = _json(
        _make_item(
            assignee=None,
            needs_review=False,
            review_reason=None,
            review_severity=None,
        )
    )
    (item,) = parse_llm_response(payload, SOURCE_TEXT)
    assert item.needs_review is True
    assert item.review_severity is ReviewSeverity.SOFT
    assert item.review_reason == "Не указан исполнитель"


def test_missing_due_date_marks_soft_review() -> None:
    payload = _json(
        _make_item(
            due_date_raw=None,
            due_date_iso=None,
            needs_review=False,
            review_reason=None,
            review_severity=None,
        )
    )
    (item,) = parse_llm_response(payload, SOURCE_TEXT)
    assert item.needs_review is True
    assert item.review_severity is ReviewSeverity.SOFT
    assert item.review_reason == "Не указан срок"


def test_ambiguous_due_date_marks_critical_review() -> None:
    payload = _json(
        _make_item(
            due_date_raw="до 25-го",
            due_date_iso=None,
            needs_review=False,
            review_reason=None,
            review_severity=None,
        )
    )
    (item,) = parse_llm_response(payload, SOURCE_TEXT)
    assert item.needs_review is True
    assert item.review_severity is ReviewSeverity.CRITICAL


def test_model_flagged_soft_is_preserved_when_no_critical_found() -> None:
    payload = _json(
        _make_item(
            needs_review=True,
            review_reason="Двусмысленная формулировка",
            review_severity="soft",
        )
    )
    (item,) = parse_llm_response(payload, SOURCE_TEXT)
    assert item.needs_review is True
    assert item.review_severity is ReviewSeverity.SOFT
    assert item.review_reason == "Двусмысленная формулировка"


def test_model_flagged_soft_escalates_to_critical_on_hallucinated_quote() -> None:
    payload = _json(
        _make_item(
            source_quote="Совершенно другая фраза, которой нет в тексте",
            confidence=0.95,
            needs_review=True,
            review_reason="Model unsure",
            review_severity="soft",
        )
    )
    (item,) = parse_llm_response(payload, SOURCE_TEXT)
    assert item.needs_review is True
    assert item.review_severity is ReviewSeverity.CRITICAL


def test_empty_actions_list_is_valid() -> None:
    result = parse_llm_response('{"actions": []}', SOURCE_TEXT)
    assert result == []


def test_priority_mapping_is_exhaustive() -> None:
    for priority in ("low", "medium", "high"):
        payload = _json(_make_item(priority=priority))
        (item,) = parse_llm_response(payload, SOURCE_TEXT)
        assert item.priority.value == priority