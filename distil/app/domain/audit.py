"""Domain entity for audit runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.enums import AuditAction, AuditStatus


@dataclass(frozen=True, slots=True)
class AuditRunEntity:
    """A single audit record for a meaningful system operation."""

    id: int
    action: AuditAction
    status: AuditStatus
    input_payload: dict[str, Any] | None
    output_payload: dict[str, Any] | None
    needs_review_count: int
    error: str | None
    duration_ms: int
    created_at: datetime