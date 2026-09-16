"""Async PostgreSQL implementation of :class:`TextRepositoryProtocol`."""

from __future__ import annotations

from typing import cast

from sqlalchemy import case, delete, func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import TextSource, TextStatus
from app.domain.text import TextEntity, TextWithStats
from app.models.action import Action
from app.models.text import Text
from app.repositories.postgres.mappers import text_to_entity


class PostgresTextRepository:
    """Async SQLAlchemy-backed text repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, source: TextSource, raw_text: str) -> TextEntity:
        orm = Text(source=source.value, raw_text=raw_text, status=TextStatus.NEW.value)
        self._session.add(orm)
        await self._session.flush()
        await self._session.refresh(orm)
        return text_to_entity(orm)

    async def get_by_id(self, text_id: int) -> TextEntity | None:
        orm = await self._session.get(Text, text_id)
        return text_to_entity(orm) if orm is not None else None

    async def list_with_stats(
        self,
        *,
        has_review_required: bool | None = None,
        source: TextSource | None = None,
        status: TextStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TextWithStats]:
        needs_review_expr = func.coalesce(
            func.sum(case((Action.needs_review.is_(True), 1), else_=0)),
            0,
        )

        stmt = (
            select(
                Text,
                func.count(Action.id).label("actions_count"),
                needs_review_expr.label("needs_review_count"),
            )
            .outerjoin(Action, Action.text_id == Text.id)
            .group_by(Text.id)
            .order_by(Text.created_at.desc(), Text.id.desc())
        )

        if source is not None:
            stmt = stmt.where(Text.source == source.value)
        if status is not None:
            stmt = stmt.where(Text.status == status.value)

        if has_review_required is True:
            stmt = stmt.having(needs_review_expr > 0)
        elif has_review_required is False:
            stmt = stmt.having(needs_review_expr == 0)

        stmt = stmt.limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        rows = result.all()

        return [
            TextWithStats(
                text=text_to_entity(row[0]),
                actions_count=int(row[1]),
                needs_review_count=int(row[2]),
            )
            for row in rows
        ]

    async def update_status(
        self, text_id: int, status: TextStatus
    ) -> TextEntity | None:
        stmt = (
            update(Text)
            .where(Text.id == text_id)
            .values(status=status.value, updated_at=func.now())
            .returning(Text)
        )
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return text_to_entity(orm) if orm is not None else None

    async def delete(self, text_id: int) -> bool:
        stmt = delete(Text).where(Text.id == text_id)
        result = await self._session.execute(stmt)
        cursor = cast(CursorResult[object], result)
        return cursor.rowcount > 0

    async def count(self) -> int:
        result = await self._session.execute(select(func.count(Text.id)))
        return int(result.scalar_one())