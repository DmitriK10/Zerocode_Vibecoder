"""Tests for :class:`ReviewService`."""

from __future__ import annotations

from datetime import date

import pytest

from app.domain.action import ActionCreate
from app.domain.enums import (
    AuditAction,
    AuditStatus,
    Priority,
    ReviewSeverity,
    ReviewStatus,
)
from app.repositories.fake import FakeActionRepository, FakeAuditRepository
from app.services.audit_service import AuditService
from app.services.exceptions import NotFoundError
from app.services.review_service import ReviewService


@pytest.fixture
def action_repo() -> FakeActionRepository:
    return FakeActionRepository()


@pytest.fixture
def audit_repo() -> FakeAuditRepository:
    return FakeAuditRepository()


@pytest.fixture
def service(
    action_repo: FakeActionRepository,
    audit_repo: FakeAuditRepository,
) -> ReviewService:
    return ReviewService(
        repository=action_repo,
        audit=AuditService(audit_repo),
    )


async def _seed_action(
    repo: FakeActionRepository,
    *,
    needs_review: bool = True,
    severity: ReviewSeverity | None = ReviewSeverity.SOFT,
) -> int:
    (action,) = await repo.create_many(
        text_id=1,
        actions=[
            ActionCreate(
                title="Needs attention",
                assignee=None,
                due_date=None,
                due_date_raw=None,
                priority=Priority.MEDIUM,
                source_quote="quote",
                confidence=0.4,
                needs_review=needs_review,
                review_reason="Не указан исполнитель" if needs_review else None,
                review_severity=severity,
            )
        ],
    )
    return action.id


async def test_confirm_clears_needs_review(
    service: ReviewService,
    action_repo: FakeActionRepository,
    audit_repo: FakeAuditRepository,
) -> None:
    action_id = await _seed_action(action_repo)
    updated = await service.confirm(action_id, reviewed_by="tester")

    assert updated.review_status is ReviewStatus.CONFIRMED
    assert updated.needs_review is False
    assert updated.reviewed_by == "tester"
    assert updated.reviewed_at is not None

    runs = await audit_repo.list()
    assert len(runs) == 1
    assert runs[0].action is AuditAction.MANUAL_REVIEW
    assert runs[0].status is AuditStatus.OK
    assert runs[0].input_payload is not None
    assert runs[0].input_payload["target"] == "confirmed"


async def test_edit_applies_changes_and_marks_edited(
    service: ReviewService,
    action_repo: FakeActionRepository,
) -> None:
    action_id = await _seed_action(action_repo)
    updated = await service.edit(
        action_id,
        title="New title",
        assignee="Ivan",
        due_date=date(2026, 9, 19),
        priority=Priority.HIGH,
        reviewed_by="tester",
    )

    assert updated.title == "New title"
    assert updated.assignee == "Ivan"
    assert updated.due_date == date(2026, 9, 19)
    assert updated.priority is Priority.HIGH
    assert updated.review_status is ReviewStatus.EDITED
    assert updated.reviewed_by == "tester"


async def test_reject_marks_rejected(
    service: ReviewService,
    action_repo: FakeActionRepository,
) -> None:
    action_id = await _seed_action(action_repo)
    updated = await service.reject(action_id)

    assert updated.review_status is ReviewStatus.REJECTED
    # Reject does not clear needs_review (it was still reviewed, but the
    # action itself is discarded).
    assert updated.needs_review is True


async def test_delete_removes_action(
    service: ReviewService,
    action_repo: FakeActionRepository,
    audit_repo: FakeAuditRepository,
) -> None:
    action_id = await _seed_action(action_repo)
    deleted = await service.delete(action_id)
    assert deleted is True
    assert await action_repo.get_by_id(action_id) is None

    runs = await audit_repo.list()
    assert len(runs) == 1
    assert runs[0].input_payload is not None
    assert runs[0].input_payload["operation"] == "delete"


async def test_confirm_missing_action_raises_and_audits(
    service: ReviewService,
    audit_repo: FakeAuditRepository,
) -> None:
    with pytest.raises(NotFoundError):
        await service.confirm(9999)

    runs = await audit_repo.list()
    assert len(runs) == 1
    assert runs[0].status is AuditStatus.ERROR


async def test_delete_missing_action_raises_and_audits(
    service: ReviewService,
    audit_repo: FakeAuditRepository,
) -> None:
    with pytest.raises(NotFoundError):
        await service.delete(9999)

    runs = await audit_repo.list()
    assert len(runs) == 1
    assert runs[0].status is AuditStatus.ERROR
    assert runs[0].input_payload is not None
    assert runs[0].input_payload["operation"] == "delete"


async def test_confirm_uses_default_reviewer(
    service: ReviewService,
    action_repo: FakeActionRepository,
) -> None:
    action_id = await _seed_action(action_repo)
    updated = await service.confirm(action_id)
    assert updated.reviewed_by == "local_user"