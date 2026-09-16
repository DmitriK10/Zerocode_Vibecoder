"""Parse raw LLM JSON into validated ``ActionCreate`` items.

Responsibilities:
* Decode JSON and validate it against :class:`LLMExtraction`.
* Verify each ``source_quote`` against the original text (fuzzy match).
* Apply the business rules for ``needs_review`` / ``review_severity``.
* Return domain DTOs (``ActionCreate``), never ORM objects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from pydantic import ValidationError

from app.domain.action import ActionCreate
from app.domain.enums import Priority, ReviewSeverity
from app.llm.exceptions import LLMParseError
from app.llm.fuzzy import verify_source_quote
from app.llm.schemas import LLMActionItem, LLMExtraction

CRITICAL_CONFIDENCE_THRESHOLD: float = 0.7


@dataclass(frozen=True, slots=True)
class QualityVerdict:
    """Outcome of applying the business quality rules to one item."""

    needs_review: bool
    review_reason: str | None
    review_severity: ReviewSeverity | None


def parse_llm_response(raw_json: str, source_text: str) -> list[ActionCreate]:
    """Parse, validate and normalise a raw LLM JSON response.

    Raises:
        LLMParseError: if the payload is not valid JSON, does not match the
            strict schema, or contains an inconsistent item.
    """
    try:
        payload: object = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise LLMParseError(
            f"LLM returned non-JSON payload: {exc.msg}", raw_payload=raw_json
        ) from exc

    try:
        extraction = LLMExtraction.model_validate(payload)
    except ValidationError as exc:
        raise LLMParseError(
            f"LLM payload failed schema validation: {exc.error_count()} error(s)",
            raw_payload=raw_json,
        ) from exc

    results: list[ActionCreate] = []
    for item in extraction.actions:
        results.append(_to_action_create(item, source_text=source_text))
    return results


def _to_action_create(item: LLMActionItem, *, source_text: str) -> ActionCreate:
    confirmed, _score = verify_source_quote(item.source_quote, source_text)
    verdict = _apply_quality_rules(item, quote_confirmed=confirmed)

    return ActionCreate(
        title=item.title,
        assignee=item.assignee or None,
        due_date=item.due_date_iso,
        due_date_raw=item.due_date_raw or None,
        priority=Priority(item.priority),
        source_quote=item.source_quote,
        confidence=item.confidence,
        needs_review=verdict.needs_review,
        review_reason=verdict.review_reason,
        review_severity=verdict.review_severity,
    )


def _apply_quality_rules(
    item: LLMActionItem, *, quote_confirmed: bool
) -> QualityVerdict:
    """Combine the model's own verdict with our stricter business rules."""
    critical_reason = _detect_critical(item, quote_confirmed=quote_confirmed)

    if item.needs_review:
        model_severity = (
            ReviewSeverity(item.review_severity)
            if item.review_severity is not None
            else ReviewSeverity.SOFT
        )
        model_reason = item.review_reason or "Модель отметила как неуверенное"

        # Escalate soft → critical if our own check found something worse.
        if critical_reason is not None and model_severity is not ReviewSeverity.CRITICAL:
            return QualityVerdict(
                needs_review=True,
                review_reason=critical_reason,
                review_severity=ReviewSeverity.CRITICAL,
            )
        return QualityVerdict(
            needs_review=True,
            review_reason=model_reason,
            review_severity=model_severity,
        )

    if critical_reason is not None:
        return QualityVerdict(
            needs_review=True,
            review_reason=critical_reason,
            review_severity=ReviewSeverity.CRITICAL,
        )

    soft_reason = _detect_soft(item)
    if soft_reason is not None:
        return QualityVerdict(
            needs_review=True,
            review_reason=soft_reason,
            review_severity=ReviewSeverity.SOFT,
        )

    return QualityVerdict(needs_review=False, review_reason=None, review_severity=None)


def _detect_critical(item: LLMActionItem, *, quote_confirmed: bool) -> str | None:
    if not quote_confirmed:
        return "Цитата не подтверждена в исходном тексте (возможна галлюцинация)"
    if item.confidence < CRITICAL_CONFIDENCE_THRESHOLD:
        return "Низкая уверенность модели (confidence < 0.7)"
    if item.due_date_raw and item.due_date_iso is None:
        return "Срок указан в неоднозначной форме и не был нормализован"
    return None


def _detect_soft(item: LLMActionItem) -> str | None:
    if item.assignee is None:
        return "Не указан исполнитель"
    if item.due_date_iso is None and item.due_date_raw is None:
        return "Не указан срок"
    return None