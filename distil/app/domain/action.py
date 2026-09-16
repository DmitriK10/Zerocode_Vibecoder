"""Domain entities for actions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.domain.enums import Priority, ReviewSeverity, ReviewStatus


@dataclass(frozen=True, slots=True)
class ActionEntity:
    """A single action extracted from a text."""

    id: int
    text_id: int
    title: str
    assignee: str | None
    due_date: date | None
    due_date_raw: str | None
    priority: Priority
    source_quote: str
    confidence: float
    needs_review: bool
    review_reason: str | None
    review_severity: ReviewSeverity | None
    review_status: ReviewStatus
    reviewed_at: datetime | None
    reviewed_by: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ActionCreate:
    """Input DTO for creating an action (no id, no timestamps)."""

    title: str
    assignee: str | None
    due_date: date | None
    due_date_raw: str | None
    priority: Priority
    source_quote: str
    confidence: float
    needs_review: bool
    review_reason: str | None
    review_severity: ReviewSeverity | None