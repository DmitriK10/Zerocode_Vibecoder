"""Pydantic models for the HTTP API.

All response models use ``from_attributes=True`` so that domain entities
(frozen dataclasses) can be validated directly, keeping the API layer
thin and free of manual mapping code.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import (
    AuditAction,
    AuditStatus,
    Priority,
    ReviewSeverity,
    ReviewStatus,
    TextSource,
    TextStatus,
)

# --------------------------------------------------------------------------
# Texts
# --------------------------------------------------------------------------


class TextCreate(BaseModel):
    """Request body for ``POST /api/texts``."""

    source: TextSource
    raw_text: str = Field(min_length=1)


class TextRead(BaseModel):
    """Full representation of a text, including the raw content."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source: TextSource
    raw_text: str
    status: TextStatus
    created_at: datetime
    updated_at: datetime


class TextSummary(BaseModel):
    """Compact representation for the showcase list (no raw_text)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source: TextSource
    status: TextStatus
    created_at: datetime
    updated_at: datetime
    actions_count: int
    needs_review_count: int

    @classmethod
    def from_stats(cls, text: Any, actions_count: int, needs_review_count: int) -> TextSummary:
        return cls(
            id=text.id,
            source=text.source,
            status=text.status,
            created_at=text.created_at,
            updated_at=text.updated_at,
            actions_count=actions_count,
            needs_review_count=needs_review_count,
        )


# --------------------------------------------------------------------------
# Actions
# --------------------------------------------------------------------------


class ActionRead(BaseModel):
    """Full representation of an extracted action."""

    model_config = ConfigDict(from_attributes=True)

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


class ActionEditRequest(BaseModel):
    """Request body for ``PATCH /api/actions/{id}``.

    Every field is optional; only provided fields are updated.
    """

    title: str | None = Field(default=None, min_length=1, max_length=200)
    assignee: str | None = Field(default=None, max_length=120)
    due_date: date | None = None
    priority: Priority | None = None


# --------------------------------------------------------------------------
# Text detail (text + actions)
# --------------------------------------------------------------------------


class TextDetail(BaseModel):
    """A text with its extracted actions."""

    text: TextRead
    actions: list[ActionRead]


# --------------------------------------------------------------------------
# Extraction
# --------------------------------------------------------------------------


class ExtractRequest(BaseModel):
    """Request body for ``POST /api/extract``."""

    text_id: int = Field(gt=0)


class ExtractResponse(BaseModel):
    """Response of ``POST /api/extract``."""

    text_id: int
    actions: list[ActionRead]
    needs_review_count: int
    duration_ms: int
    injection_detected: bool


# --------------------------------------------------------------------------
# Audit
# --------------------------------------------------------------------------


class AuditRunRead(BaseModel):
    """A single audit record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    action: AuditAction
    status: AuditStatus
    input_payload: dict[str, Any] | None
    output_payload: dict[str, Any] | None
    needs_review_count: int
    error: str | None
    duration_ms: int
    created_at: datetime