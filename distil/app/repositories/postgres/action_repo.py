"""Async PostgreSQL implementation of :class:`ActionRepositoryProtocol`."""

from __future__ import annotations

from datetime import date, datetime
from typing import cast

from sqlalchemy import delete, func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.action import ActionCreate, ActionEntity
from app.domain.enums import Priority, ReviewStatus
from app.models.action import Action
from app.repositories.postgres.mappers import action_to_entity


class PostgresActionRepository:
    """Async SQLAlchemy-backed action repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_many(
        self, *, text_id: int, actions: list[ActionCreate]
    ) -> list[ActionEntity]:
        if not actions:
            return []

        orms: list[Action] = []
        for item in actions:
            orm = Action(
                text_id=text_id,
                title=item.title,
                assignee=item.assignee,
                due_date=item.due_date,
                due_date_raw=item.due_date_raw,
                priority=item.priority.value,
                source_quote=item.source_quote,
                confidence=item.confidence,
                needs_review=item.needs_review,
                review_reason=item.review_reason,
                review_severity=(
                    item.review_severity.value if item.review_severity else None
                ),
                review_status=ReviewStatus.PENDING.value,
            )
            self._session.add(orm)
            orms.append(orm)

        await self._session.flush()
        for orm in orms:
            await self._session.refresh(orm)
        return [action_to_entity(orm) for orm in orms]

    async def get_by_id(self, action_id: int) -> ActionEntity | None:
        orm = await self._session.get(Action, action_id)
        return action_to_entity(orm) if orm is not None else None

    async def list_by_text(self, text_id: int) -> list[ActionEntity]:
        stmt = (
            select(Action)
            .where(Action.text_id == text_id)
            .order_by(Action.id.asc())
        )
        result = await self._session.execute(stmt)
        return [action_to_entity(orm) for orm in result.scalars().all()]

    async def delete_by_text(self, text_id: int) -> int:
        stmt = delete(Action).where(Action.text_id == text_id)
        result = await self._session.execute(stmt)
        cursor = cast(CursorResult[object], result)
        return int(cursor.rowcount or 0)

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
        values: dict[str, object] = {
            "review_status": review_status.value,
            "reviewed_by": reviewed_by,
            "reviewed_at": reviewed_at,
            "updated_at": func.now(),
        }

        if review_status is ReviewStatus.CONFIRMED:
            values["needs_review"] = False

        if title is not None:
            values["title"] = title
        if assignee is not None:
            values["assignee"] = assignee
        if due_date is not None:
            values["due_date"] = due_date
        if priority is not None:
            values["priority"] = priority.value

        stmt = (
            update(Action)
            .where(Action.id == action_id)
            .values(**values)
            .returning(Action)
        )
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return action_to_entity(orm) if orm is not None else None

    async def delete(self, action_id: int) -> bool:
        stmt = delete(Action).where(Action.id == action_id)
        result = await self._session.execute(stmt)
        cursor = cast(CursorResult[object], result)
        return cursor.rowcount > 0

    async def count_by_text(self, text_id: int) -> tuple[int, int]:
        total_stmt = select(func.count(Action.id)).where(Action.text_id == text_id)
        review_stmt = select(func.count(Action.id)).where(
            Action.text_id == text_id, Action.needs_review.is_(True)
        )
        total = int((await self._session.execute(total_stmt)).scalar_one())
        review = int((await self._session.execute(review_stmt)).scalar_one())
        return total, review