"""ReviewService — manual review workflow.

Every mutation of an action's review state goes through this service so
that:

* the status transition is applied consistently,
* the ``reviewed_at`` / ``reviewed_by`` fields are always filled,
* a ``manual_review`` audit entry is written.

Supported transitions:
* ``confirm`` — accept the action as-is (``needs_review`` cleared).
* ``edit``    — apply field changes and mark as ``edited``.
* ``reject``  — mark as ``rejected``.
* ``delete``  — remove the action entirely.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from app.domain.action import ActionEntity
from app.domain.enums import AuditAction, Priority, ReviewStatus
from app.repositories.protocols import ActionRepositoryProtocol
from app.services.audit_service import AuditService
from app.services.exceptions import NotFoundError
from app.services.timing import elapsed_ms, now_monotonic

DEFAULT_REVIEWER: str = "local_user"


class ReviewService:
    """Manual review of extracted actions."""

    def __init__(
        self,
        *,
        repository: ActionRepositoryProtocol,
        audit: AuditService,
        default_reviewer: str = DEFAULT_REVIEWER,
    ) -> None:
        self._repo = repository
        self._audit = audit
        self._default_reviewer = default_reviewer

    async def confirm(
        self,
        action_id: int,
        *,
        reviewed_by: str | None = None,
    ) -> ActionEntity:
        """Confirm the action and clear ``needs_review``."""
        return await self._transition(
            action_id,
            target=ReviewStatus.CONFIRMED,
            reviewed_by=reviewed_by or self._default_reviewer,
        )

    async def edit(
        self,
        action_id: int,
        *,
        title: str | None = None,
        assignee: str | None = None,
        due_date: date | None = None,
        priority: Priority | None = None,
        reviewed_by: str | None = None,
    ) -> ActionEntity:
        """Apply edits and mark the action as ``edited``."""
        return await self._transition(
            action_id,
            target=ReviewStatus.EDITED,
            reviewed_by=reviewed_by or self._default_reviewer,
            title=title,
            assignee=assignee,
            due_date=due_date,
            priority=priority,
        )

    async def reject(
        self,
        action_id: int,
        *,
        reviewed_by: str | None = None,
    ) -> ActionEntity:
        """Mark the action as ``rejected``."""
        return await self._transition(
            action_id,
            target=ReviewStatus.REJECTED,
            reviewed_by=reviewed_by or self._default_reviewer,
        )

    async def delete(
        self,
        action_id: int,
        *,
        reviewed_by: str | None = None,
    ) -> bool:
        """Permanently delete the action and audit the deletion."""
        started = now_monotonic()
        existing = await self._repo.get_by_id(action_id)
        if existing is None:
            await self._audit.record_error(
                action=AuditAction.MANUAL_REVIEW,
                duration_ms=elapsed_ms(started),
                error=f"Action {action_id} not found",
                input_payload={"action_id": action_id, "operation": "delete"},
            )
            raise NotFoundError(f"Action {action_id} not found")

        deleted = await self._repo.delete(action_id)

        await self._audit.record_success(
            action=AuditAction.MANUAL_REVIEW,
            duration_ms=elapsed_ms(started),
            input_payload={
                "action_id": action_id,
                "operation": "delete",
                "reviewed_by": reviewed_by or self._default_reviewer,
            },
            output_payload={"deleted": deleted},
        )
        return deleted

    # -- internals --------------------------------------------------------
    async def _transition(
        self,
        action_id: int,
        *,
        target: ReviewStatus,
        reviewed_by: str,
        title: str | None = None,
        assignee: str | None = None,
        due_date: date | None = None,
        priority: Priority | None = None,
    ) -> ActionEntity:
        started = now_monotonic()

        existing = await self._repo.get_by_id(action_id)
        if existing is None:
            await self._audit.record_error(
                action=AuditAction.MANUAL_REVIEW,
                duration_ms=elapsed_ms(started),
                error=f"Action {action_id} not found",
                input_payload={
                    "action_id": action_id,
                    "target": target.value,
                },
            )
            raise NotFoundError(f"Action {action_id} not found")

        updated = await self._repo.update_review(
            action_id,
            title=title,
            assignee=assignee,
            due_date=due_date,
            priority=priority,
            review_status=target,
            reviewed_by=reviewed_by,
            reviewed_at=datetime.now(tz=UTC),
        )

        # ``update_review`` returns ``None`` only if the row vanished
        # between the get and the update — treat it as not found.
        if updated is None:
            await self._audit.record_error(
                action=AuditAction.MANUAL_REVIEW,
                duration_ms=elapsed_ms(started),
                error=f"Action {action_id} disappeared during update",
                input_payload={
                    "action_id": action_id,
                    "target": target.value,
                },
            )
            raise NotFoundError(f"Action {action_id} not found")

        await self._audit.record_success(
            action=AuditAction.MANUAL_REVIEW,
            duration_ms=elapsed_ms(started),
            input_payload={
                "action_id": action_id,
                "target": target.value,
                "reviewed_by": reviewed_by,
            },
            output_payload={"review_status": updated.review_status.value},
        )
        return updated