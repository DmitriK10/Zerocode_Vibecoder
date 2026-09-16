"""Async PostgreSQL implementation of :class:`AuditRepositoryProtocol`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.audit import AuditRunEntity
from app.domain.enums import AuditAction, AuditStatus
from app.models.audit import AuditRun
from app.repositories.postgres.mappers import audit_to_entity


class PostgresAuditRepository:
    """Async SQLAlchemy-backed audit repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        orm = AuditRun(
            action=action.value,
            status=status.value,
            duration_ms=duration_ms,
            input_payload=input_payload,
            output_payload=output_payload,
            needs_review_count=needs_review_count,
            error=error,
        )
        self._session.add(orm)
        await self._session.flush()
        await self._session.refresh(orm)
        return audit_to_entity(orm)

    async def list(
        self,
        *,
        status: AuditStatus | None = None,
        action: AuditAction | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditRunEntity]:
        stmt = select(AuditRun).order_by(AuditRun.created_at.desc(), AuditRun.id.desc())
        if status is not None:
            stmt = stmt.where(AuditRun.status == status.value)
        if action is not None:
            stmt = stmt.where(AuditRun.action == action.value)
        stmt = stmt.limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        return [audit_to_entity(orm) for orm in result.scalars().all()]

    async def get_by_id(self, audit_id: int) -> AuditRunEntity | None:
        orm = await self._session.get(AuditRun, audit_id)
        return audit_to_entity(orm) if orm is not None else None

    async def delete_older_than(self, *, days: int) -> int:
        if days <= 0:
            return 0
        cutoff = datetime.now(tz=UTC) - timedelta(days=days)
        stmt = delete(AuditRun).where(AuditRun.created_at < cutoff)
        result = await self._session.execute(stmt)
        cursor = cast(CursorResult[object], result)
        return int(cursor.rowcount or 0)