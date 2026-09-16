"""In-memory audit repository."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.domain.audit import AuditRunEntity
from app.domain.enums import AuditAction, AuditStatus


class FakeAuditRepository:
    """A dict-backed audit repository for tests."""

    def __init__(self) -> None:
        self._items: dict[int, AuditRunEntity] = {}
        self._next_id: int = 1

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
        entity = AuditRunEntity(
            id=self._next_id,
            action=action,
            status=status,
            input_payload=input_payload,
            output_payload=output_payload,
            needs_review_count=needs_review_count,
            error=error,
            duration_ms=duration_ms,
            created_at=datetime.now(tz=UTC),
        )
        self._items[entity.id] = entity
        self._next_id += 1
        return entity

    async def list(
        self,
        *,
        status: AuditStatus | None = None,
        action: AuditAction | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditRunEntity]:
        items = sorted(
            self._items.values(), key=lambda a: (a.created_at, a.id), reverse=True
        )
        if status is not None:
            items = [a for a in items if a.status is status]
        if action is not None:
            items = [a for a in items if a.action is action]
        return items[offset : offset + limit]

    async def get_by_id(self, audit_id: int) -> AuditRunEntity | None:
        return self._items.get(audit_id)

    async def delete_older_than(self, *, days: int) -> int:
        if days <= 0:
            return 0
        cutoff = datetime.now(tz=UTC) - timedelta(days=days)
        to_delete = [k for k, v in self._items.items() if v.created_at < cutoff]
        for key in to_delete:
            del self._items[key]
        return len(to_delete)