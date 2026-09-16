"""Tests for Fake (in-memory) repositories.

Ensures both implementations honour the same protocol contracts — this is
how we prove substitutability (Liskov) and that services can be tested
without a database.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.action import ActionCreate
from app.domain.enums import (
    AuditAction,
    AuditStatus,
    Priority,
    ReviewSeverity,
    ReviewStatus,
    TextSource,
    TextStatus,
)
from app.repositories.fake import (
    FakeActionRepository,
    FakeAuditRepository,
    FakeTextRepository,
)


async def test_fake_text_create_and_get() -> None:
    repo = FakeTextRepository()
    created = await repo.create(
        source=TextSource.EMAIL, raw_text="A sufficiently long raw text for tests."
    )
    assert created.id == 1
    assert created.status is TextStatus.NEW
    assert await repo.get_by_id(1) == created
    assert await repo.count() == 1


async def test_fake_text_update_and_delete() -> None:
    repo = FakeTextRepository()
    created = await repo.create(
        source=TextSource.NOTE, raw_text="A sufficiently long raw text for tests."
    )
    updated = await repo.update_status(created.id, TextStatus.EXTRACTED)
    assert updated is not None
    assert updated.status is TextStatus.EXTRACTED
    assert await repo.delete(created.id) is True
    assert await repo.get_by_id(created.id) is None


async def test_fake_text_list_with_stats() -> None:
    text_repo = FakeTextRepository()
    action_repo = FakeActionRepository()

    t1 = await text_repo.create(
        source=TextSource.EMAIL, raw_text="A sufficiently long raw text for tests."
    )
    t2 = await text_repo.create(
        source=TextSource.NOTE, raw_text="Another sufficiently long text for tests."
    )

    await action_repo.create_many(
        text_id=t1.id,
        actions=[
            ActionCreate(
                title="Review me",
                assignee=None,
                due_date=None,
                due_date_raw=None,
                priority=Priority.MEDIUM,
                source_quote="q",
                confidence=0.5,
                needs_review=True,
                review_reason="r",
                review_severity=ReviewSeverity.SOFT,
            )
        ],
    )
    await action_repo.create_many(
        text_id=t2.id,
        actions=[
            ActionCreate(
                title="Clean",
                assignee="Ivan",
                due_date=None,
                due_date_raw=None,
                priority=Priority.LOW,
                source_quote="q",
                confidence=0.9,
                needs_review=False,
                review_reason=None,
                review_severity=None,
            )
        ],
    )

    # Wire a stats provider so list_with_stats can aggregate.
    async def _noop() -> None:  # pragma: no cover - helper placeholder
        return None

    _ = _noop  # silence linters; async signature not required for provider

    def stats_provider(text_id: int) -> tuple[int, int]:
        # Synchronous provider — matches FakeTextRepository contract.
        return _sync_stats(action_repo, text_id)

    text_repo.set_stats_provider(stats_provider)

    only_review = await text_repo.list_with_stats(has_review_required=True)
    assert len(only_review) == 1
    assert only_review[0].text.id == t1.id
    assert only_review[0].needs_review_count == 1

    only_clean = await text_repo.list_with_stats(has_review_required=False)
    assert len(only_clean) == 1
    assert only_clean[0].text.id == t2.id


def _sync_stats(action_repo: FakeActionRepository, text_id: int) -> tuple[int, int]:
    # FakeActionRepository stores everything in memory; safe to inspect
    # synchronously for test purposes.
    items = [a for a in action_repo._items.values() if a.text_id == text_id]  # noqa: SLF001
    return len(items), sum(1 for a in items if a.needs_review)


async def test_fake_action_review_flow() -> None:
    repo = FakeActionRepository()
    (action,) = await repo.create_many(
        text_id=1,
        actions=[
            ActionCreate(
                title="Needs confirm",
                assignee=None,
                due_date=None,
                due_date_raw=None,
                priority=Priority.MEDIUM,
                source_quote="q",
                confidence=0.4,
                needs_review=True,
                review_reason="Не указан исполнитель",
                review_severity=ReviewSeverity.SOFT,
            )
        ],
    )
    updated = await repo.update_review(
        action.id,
        review_status=ReviewStatus.CONFIRMED,
        reviewed_by="local_user",
        reviewed_at=datetime.now(tz=UTC),
    )
    assert updated is not None
    assert updated.needs_review is False
    assert updated.review_status is ReviewStatus.CONFIRMED

    total, review = await repo.count_by_text(1)
    assert total == 1
    assert review == 0


async def test_fake_audit_create_list_delete() -> None:
    repo = FakeAuditRepository()
    await repo.create(
        action=AuditAction.CREATE_TEXT,
        status=AuditStatus.OK,
        duration_ms=3,
    )
    await repo.create(
        action=AuditAction.EXTRACT_ACTIONS,
        status=AuditStatus.ERROR,
        duration_ms=500,
        error="boom",
    )
    assert len(await repo.list()) == 2
    assert len(await repo.list(status=AuditStatus.ERROR)) == 1
    # Nothing older than 30 days in a fresh repository.
    assert await repo.delete_older_than(days=30) == 0