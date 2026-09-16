"""In-memory action repository."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime

from app.domain.action import ActionCreate, ActionEntity
from app.domain.enums import Priority, ReviewStatus


class FakeActionRepository:
    """A dict-backed action repository for tests."""

    def __init__(self) -> None:
        self._items: dict[int, ActionEntity] = {}
        self._next_id: int = 1

    # -- Public test API -------------------------------------------------

    def all_entities(self) -> list[ActionEntity]:
        """Return a snapshot of every stored action."""
        return list(self._items.values())

    # -- Protocol --------------------------------------------------------

    async def create_many(
        self, *, text_id: int, actions: list[ActionCreate]
    ) -> list[ActionEntity]:
        now = datetime.now(tz=UTC)
        created: list[ActionEntity] = []
        for item in actions:
            entity = ActionEntity(
                id=self._next_id,
                text_id=text_id,
                title=item.title,
                assignee=item.assignee,
                due_date=item.due_date,
                due_date_raw=item.due_date_raw,
                priority=item.priority,
                source_quote=item.source_quote,
                confidence=item.confidence,
                needs_review=item.needs_review,
                review_reason=item.review_reason,
                review_severity=item.review_severity,
                review_status=ReviewStatus.PENDING,
                reviewed_at=None,
                reviewed_by=None,
                created_at=now,
                updated_at=now,
            )
            self._items[entity.id] = entity
            self._next_id += 1
            created.append(entity)
        return created

    async def get_by_id(self, action_id: int) -> ActionEntity | None:
        return self._items.get(action_id)

    async def list_by_text(self, text_id: int) -> list[ActionEntity]:
        return sorted(
            (a for a in self._items.values() if a.text_id == text_id),
            key=lambda a: a.id,
        )

    async def delete_by_text(self, text_id: int) -> int:
        to_delete = [k for k, v in self._items.items() if v.text_id == text_id]
        for k in to_delete:
            del self._items[k]
        return len(to_delete)

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
        current = self._items.get(action_id)
        if current is None:
            return None

        needs_review = current.needs_review
        if review_status is ReviewStatus.CONFIRMED:
            needs_review = False

        updated = replace(
            current,
            title=title if title is not None else current.title,
            assignee=assignee if assignee is not None else current.assignee,
            due_date=due_date if due_date is not None else current.due_date,
            priority=priority if priority is not None else current.priority,
            review_status=review_status,
            needs_review=needs_review,
            reviewed_at=reviewed_at,
            reviewed_by=reviewed_by,
            updated_at=datetime.now(tz=UTC),
        )
        self._items[action_id] = updated
        return updated

    async def delete(self, action_id: int) -> bool:
        return self._items.pop(action_id, None) is not None

    async def count_by_text(self, text_id: int) -> tuple[int, int]:
        items = [a for a in self._items.values() if a.text_id == text_id]
        return len(items), sum(1 for a in items if a.needs_review)