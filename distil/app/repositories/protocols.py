"""Abstract repository interfaces (Dependency Inversion)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Protocol

from app.domain.action import ActionCreate, ActionEntity
from app.domain.audit import AuditRunEntity
from app.domain.enums import (
    AuditAction,
    AuditStatus,
    Priority,
    ReviewStatus,
    TextSource,
    TextStatus,
)
from app.domain.text import TextEntity, TextWithStats


class TextRepositoryProtocol(Protocol):
    """Persistence operations for :class:`TextEntity`."""

    async def create(self, *, source: TextSource, raw_text: str) -> TextEntity:
        ...

    async def get_by_id(self, text_id: int) -> TextEntity | None:
        ...

    async def list_with_stats(
        self,
        *,
        has_review_required: bool | None = None,
        source: TextSource | None = None,
        status: TextStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TextWithStats]:
        ...

    async def update_status(
        self, text_id: int, status: TextStatus
    ) -> TextEntity | None:
        ...

    async def delete(self, text_id: int) -> bool:
        ...

    async def count(self) -> int:
        ...


class ActionRepositoryProtocol(Protocol):
    """Persistence operations for :class:`ActionEntity`."""

    async def create_many(
        self, *, text_id: int, actions: list[ActionCreate]
    ) -> list[ActionEntity]:
        ...

    async def get_by_id(self, action_id: int) -> ActionEntity | None:
        ...

    async def list_by_text(self, text_id: int) -> list[ActionEntity]:
        ...

    async def delete_by_text(self, text_id: int) -> int:
        """Delete all actions attached to a text. Returns count."""
        ...

    async def update_review(
        self,
        action_id: int,
        *,
        title: str | None = None,
        assignee: str | None = None,
        due_date: date | None = None,
        priority: Priority | None = None,
        review_status: ReviewStatus,
        reviewed_by: str,
        reviewed_at: datetime,
    ) -> ActionEntity | None:
        ...

    async def delete(self, action_id: int) -> bool:
        ...

    async def count_by_text(self, text_id: int) -> tuple[int, int]:
        ...


class AuditRepositoryProtocol(Protocol):
    """Persistence operations for :class:`AuditRunEntity`."""

    async def create(
        self,
        *,
        action: AuditAction,
        status: AuditStatus,
        duration_ms: int,
        input_payload: dict[str, Any] | None = None,
        output_payload: dict[str, Any] | None = None,
        needs_review_count: int = 0,
        error: str | None = None,
    ) -> AuditRunEntity:
        ...

    async def list(
        self,
        *,
        status: AuditStatus | None = None,
        action: AuditAction | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditRunEntity]:
        ...

    async def get_by_id(self, audit_id: int) -> AuditRunEntity | None:
        ...

    async def delete_older_than(self, *, days: int) -> int:
        ...