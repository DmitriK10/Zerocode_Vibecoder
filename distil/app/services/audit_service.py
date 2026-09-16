"""AuditService — a single point of truth for writing ``audit_runs``.

Every meaningful operation in the system goes through this service. It is
the only place that constructs :class:`AuditRunEntity` objects, which keeps
call sites clean and audit semantics consistent.
"""

from __future__ import annotations

from typing import Any

from app.domain.audit import AuditRunEntity
from app.domain.enums import AuditAction, AuditStatus
from app.repositories.protocols import AuditRepositoryProtocol


class AuditService:
    """Records operations into ``audit_runs``."""

    def __init__(self, repository: AuditRepositoryProtocol) -> None:
        self._repo = repository

    async def record_success(
        self,
        *,
        action: AuditAction,
        duration_ms: int,
        input_payload: dict[str, Any] | None = None,
        output_payload: dict[str, Any] | None = None,
        needs_review_count: int = 0,
    ) -> AuditRunEntity:
        """Record a successful operation."""
        return await self._repo.create(
            action=action,
            status=AuditStatus.OK,
            duration_ms=duration_ms,
            input_payload=input_payload,
            output_payload=output_payload,
            needs_review_count=needs_review_count,
        )

    async def record_error(
        self,
        *,
        action: AuditAction,
        duration_ms: int,
        error: str,
        input_payload: dict[str, Any] | None = None,
    ) -> AuditRunEntity:
        """Record a failed operation."""
        return await self._repo.create(
            action=action,
            status=AuditStatus.ERROR,
            duration_ms=duration_ms,
            input_payload=input_payload,
            error=error,
        )

    async def list_runs(
        self,
        *,
        status: AuditStatus | None = None,
        action: AuditAction | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditRunEntity]:
        """Return audit records, newest first."""
        return await self._repo.list(
            status=status,
            action=action,
            limit=limit,
            offset=offset,
        )

    async def get_by_id(self, audit_id: int) -> AuditRunEntity | None:
        """Return a single audit record by id, or ``None``."""
        return await self._repo.get_by_id(audit_id)