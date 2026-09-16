"""Tests for Postgres repositories.

These tests run against in-memory async SQLite via the portable
``JSONType`` and identical DDL — the SQLAlchemy layer is dialect-neutral
enough for this to work. Real PostgreSQL behaviour is exercised in CI
via a dedicated service container.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.repositories.postgres import (
    PostgresActionRepository,
    PostgresAuditRepository,
    PostgresTextRepository,
)


@pytest.fixture
def text_repo(session: AsyncSession) -> PostgresTextRepository:
    return PostgresTextRepository(session)


@pytest.fixture
def action_repo(session: AsyncSession) -> PostgresActionRepository:
    return PostgresActionRepository(session)


@pytest.fixture
def audit_repo(session: AsyncSession) -> PostgresAuditRepository:
    return PostgresAuditRepository(session)


# ------------------------------------------------------------------ texts


async def test_text_repo_create_and_get(text_repo: PostgresTextRepository) -> None:
    created = await text_repo.create(
        source=TextSource.EMAIL, raw_text="A sufficiently long raw text for tests."
    )
    assert created.id > 0
    assert created.source is TextSource.EMAIL
    assert created.status is TextStatus.NEW

    fetched = await text_repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id


async def test_text_repo_update_status(text_repo: PostgresTextRepository) -> None:
    created = await text_repo.create(
        source=TextSource.NOTE, raw_text="A sufficiently long raw text for tests."
    )
    updated = await text_repo.update_status(created.id, TextStatus.EXTRACTED)
    assert updated is not None
    assert updated.status is TextStatus.EXTRACTED


async def test_text_repo_delete_cascades(session: AsyncSession) -> None:
    text_repo = PostgresTextRepository(session)
    action_repo = PostgresActionRepository(session)

    text = await text_repo.create(
        source=TextSource.NOTE, raw_text="A sufficiently long raw text for tests."
    )
    await action_repo.create_many(
        text_id=text.id,
        actions=[
            ActionCreate(
                title="Do X",
                assignee=None,
                due_date=None,
                due_date_raw=None,
                priority=Priority.MEDIUM,
                source_quote="A sufficiently long",
                confidence=0.9,
                needs_review=False,
                review_reason=None,
                review_severity=None,
            )
        ],
    )
    assert await text_repo.delete(text.id) is True
    assert await text_repo.get_by_id(text.id) is None
    assert await action_repo.list_by_text(text.id) == []


async def test_text_repo_list_with_stats_filter(
    session: AsyncSession,
) -> None:
    text_repo = PostgresTextRepository(session)
    action_repo = PostgresActionRepository(session)

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
                title="Needs review",
                assignee=None,
                due_date=None,
                due_date_raw=None,
                priority=Priority.MEDIUM,
                source_quote="A sufficiently long",
                confidence=0.5,
                needs_review=True,
                review_reason="Не указан ответственный",
                review_severity=ReviewSeverity.SOFT,
            )
        ],
    )
    await action_repo.create_many(
        text_id=t2.id,
        actions=[
            ActionCreate(
                title="Clean action",
                assignee="Ivan",
                due_date=None,
                due_date_raw=None,
                priority=Priority.HIGH,
                source_quote="Another sufficiently long",
                confidence=0.95,
                needs_review=False,
                review_reason=None,
                review_severity=None,
            )
        ],
    )
    await session.commit()

    with_review = await text_repo.list_with_stats(has_review_required=True)
    assert {row.text.id for row in with_review} == {t1.id}
    assert with_review[0].needs_review_count == 1
    assert with_review[0].actions_count == 1

    without_review = await text_repo.list_with_stats(has_review_required=False)
    assert {row.text.id for row in without_review} == {t2.id}


# --------------------------------------------------------------- actions


async def test_action_repo_create_many_and_list(
    session: AsyncSession, text_repo: PostgresTextRepository
) -> None:
    text = await text_repo.create(
        source=TextSource.NOTE, raw_text="A sufficiently long raw text for tests."
    )
    repo = PostgresActionRepository(session)
    created = await repo.create_many(
        text_id=text.id,
        actions=[
            ActionCreate(
                title="A1",
                assignee=None,
                due_date=date(2026, 9, 19),
                due_date_raw="к пятнице",
                priority=Priority.HIGH,
                source_quote="quote 1",
                confidence=0.8,
                needs_review=False,
                review_reason=None,
                review_severity=None,
            ),
            ActionCreate(
                title="A2",
                assignee=None,
                due_date=None,
                due_date_raw=None,
                priority=Priority.MEDIUM,
                source_quote="quote 2",
                confidence=0.5,
                needs_review=True,
                review_reason="Не указан срок",
                review_severity=ReviewSeverity.SOFT,
            ),
        ],
    )
    assert len(created) == 2
    listed = await repo.list_by_text(text.id)
    assert [a.title for a in listed] == ["A1", "A2"]


async def test_action_repo_update_review_confirm(
    session: AsyncSession, text_repo: PostgresTextRepository
) -> None:
    text = await text_repo.create(
        source=TextSource.NOTE, raw_text="A sufficiently long raw text for tests."
    )
    repo = PostgresActionRepository(session)
    (action,) = await repo.create_many(
        text_id=text.id,
        actions=[
            ActionCreate(
                title="Needs confirm",
                assignee=None,
                due_date=None,
                due_date_raw=None,
                priority=Priority.MEDIUM,
                source_quote="quote",
                confidence=0.5,
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
    assert updated.review_status is ReviewStatus.CONFIRMED
    assert updated.needs_review is False
    assert updated.reviewed_by == "local_user"


async def test_action_repo_count_by_text(
    session: AsyncSession, text_repo: PostgresTextRepository
) -> None:
    text = await text_repo.create(
        source=TextSource.NOTE, raw_text="A sufficiently long raw text for tests."
    )
    repo = PostgresActionRepository(session)
    await repo.create_many(
        text_id=text.id,
        actions=[
            ActionCreate(
                title="A1",
                assignee=None,
                due_date=None,
                due_date_raw=None,
                priority=Priority.LOW,
                source_quote="q1",
                confidence=0.5,
                needs_review=True,
                review_reason="r",
                review_severity=ReviewSeverity.SOFT,
            ),
            ActionCreate(
                title="A2",
                assignee="Ivan",
                due_date=None,
                due_date_raw=None,
                priority=Priority.LOW,
                source_quote="q2",
                confidence=0.9,
                needs_review=False,
                review_reason=None,
                review_severity=None,
            ),
        ],
    )
    total, review = await repo.count_by_text(text.id)
    assert total == 2
    assert review == 1


# ----------------------------------------------------------------- audit


async def test_audit_repo_create_and_list(
    audit_repo: PostgresAuditRepository,
) -> None:
    await audit_repo.create(
        action=AuditAction.CREATE_TEXT,
        status=AuditStatus.OK,
        duration_ms=5,
        input_payload={"source": "email"},
    )
    await audit_repo.create(
        action=AuditAction.EXTRACT_ACTIONS,
        status=AuditStatus.ERROR,
        duration_ms=1200,
        error="Upstream timeout",
    )
    all_runs = await audit_repo.list()
    assert len(all_runs) == 2

    errors = await audit_repo.list(status=AuditStatus.ERROR)
    assert len(errors) == 1
    assert errors[0].error == "Upstream timeout"


async def test_audit_repo_get_by_id(audit_repo: PostgresAuditRepository) -> None:
    created = await audit_repo.create(
        action=AuditAction.CREATE_TEXT,
        status=AuditStatus.OK,
        duration_ms=1,
    )
    fetched = await audit_repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id