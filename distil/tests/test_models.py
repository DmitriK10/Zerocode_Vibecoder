"""Tests for ORM models and database-level constraints.

Runs against an in-memory async SQLite database. The portable ``JSONType``
used in :class:`AuditRun` degrades gracefully to plain ``JSON`` there, and
``BigIntType`` degrades to ``INTEGER`` so PKs autoincrement via rowid.

Async SQLAlchemy note
---------------------
Relationships in async sessions must be loaded explicitly (``selectinload``,
``joinedload`` or ``refresh(..., attribute_names=[...])``). Plain lazy
loading is forbidden and raises ``MissingGreenlet``.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Action, AuditRun, Text

# --------------------------------------------------------------------- texts


async def test_text_insert_and_defaults(session: AsyncSession) -> None:
    text = Text(source="email", raw_text="Hello world, this is a valid text.")
    session.add(text)
    await session.commit()
    await session.refresh(text)

    assert text.id is not None
    assert text.status == "new"
    assert text.created_at is not None
    assert text.updated_at is not None


async def test_text_source_check_constraint(session: AsyncSession) -> None:
    session.add(Text(source="telegram", raw_text="A sufficiently long raw text."))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_text_raw_text_min_length(session: AsyncSession) -> None:
    session.add(Text(source="note", raw_text="short"))
    with pytest.raises(IntegrityError):
        await session.commit()


# ------------------------------------------------------------------- actions


async def test_action_defaults_and_relationship(session: AsyncSession) -> None:
    text = Text(
        source="email",
        raw_text="Please do X by Friday, this is important and urgent.",
    )
    text.actions.append(
        Action(
            title="Do X",
            priority="high",
            source_quote="Please do X by Friday",
            confidence=0.9,
        )
    )
    session.add(text)
    await session.commit()

    # Re-query with explicit eager loading — the only safe way to read a
    # relationship in an async session after commit.
    stmt = (
        select(Text)
        .where(Text.id == text.id)
        .options(selectinload(Text.actions))
    )
    loaded = (await session.execute(stmt)).scalar_one()

    assert len(loaded.actions) == 1
    action = loaded.actions[0]
    assert action.needs_review is False
    assert action.review_status == "pending"
    assert action.priority == "high"
    assert action.confidence == pytest.approx(0.9)


async def test_action_confidence_out_of_range(session: AsyncSession) -> None:
    text = Text(source="note", raw_text="A sufficiently long raw text for tests.")
    session.add(text)
    await session.commit()

    session.add(
        Action(
            text_id=text.id,
            title="Bad action",
            priority="low",
            source_quote="A sufficiently long",
            confidence=1.5,
        )
    )
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_action_priority_check_constraint(session: AsyncSession) -> None:
    text = Text(source="note", raw_text="A sufficiently long raw text for tests.")
    session.add(text)
    await session.commit()

    session.add(
        Action(
            text_id=text.id,
            title="Bad priority",
            priority="urgent",
            source_quote="A sufficiently long",
            confidence=0.5,
        )
    )
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_action_review_status_check_constraint(session: AsyncSession) -> None:
    text = Text(source="note", raw_text="A sufficiently long raw text for tests.")
    session.add(text)
    await session.commit()

    session.add(
        Action(
            text_id=text.id,
            title="Bad status",
            priority="medium",
            source_quote="A sufficiently long",
            confidence=0.5,
            review_status="maybe",
        )
    )
    with pytest.raises(IntegrityError):
        await session.commit()


# ---------------------------------------------------------------- audit_runs


async def test_audit_run_defaults(session: AsyncSession) -> None:
    run = AuditRun(action="create_text", status="ok", duration_ms=12)
    session.add(run)
    await session.commit()
    await session.refresh(run)

    assert run.id is not None
    assert run.needs_review_count == 0
    assert run.error is None
    assert run.input_payload is None
    assert run.output_payload is None


async def test_audit_run_status_check_constraint(session: AsyncSession) -> None:
    session.add(AuditRun(action="extract_actions", status="needs_review", duration_ms=1))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_audit_run_negative_duration_rejected(session: AsyncSession) -> None:
    session.add(AuditRun(action="extract_actions", status="ok", duration_ms=-1))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_audit_run_stores_json_payloads(session: AsyncSession) -> None:
    run = AuditRun(
        action="extract_actions",
        status="ok",
        duration_ms=42,
        needs_review_count=2,
        input_payload={"text_id": 1},
        output_payload={"actions_count": 3},
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)

    assert run.input_payload == {"text_id": 1}
    assert run.output_payload == {"actions_count": 3}
    assert run.needs_review_count == 2