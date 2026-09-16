"""In-memory text repository."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from app.domain.enums import TextSource, TextStatus
from app.domain.text import TextEntity, TextWithStats


class FakeTextRepository:
    """A dict-backed text repository for tests.

    The repository also exposes a hook so tests can inject a callable that
    counts actions for a given text (to emulate ``actions_count`` and
    ``needs_review_count`` in :meth:`list_with_stats`).
    """

    def __init__(
        self,
        *,
        stats_provider: Callable[[int], tuple[int, int]] | None = None,
    ) -> None:
        self._items: dict[int, TextEntity] = {}
        self._next_id: int = 1
        self._stats_provider: Callable[[int], tuple[int, int]] | None = (
            stats_provider
        )

    def set_stats_provider(
        self, provider: Callable[[int], tuple[int, int]]
    ) -> None:
        self._stats_provider = provider

    async def create(self, *, source: TextSource, raw_text: str) -> TextEntity:
        now = datetime.now(tz=UTC)
        entity = TextEntity(
            id=self._next_id,
            source=source,
            raw_text=raw_text,
            status=TextStatus.NEW,
            created_at=now,
            updated_at=now,
        )
        self._items[entity.id] = entity
        self._next_id += 1
        return entity

    async def get_by_id(self, text_id: int) -> TextEntity | None:
        return self._items.get(text_id)

    async def list_with_stats(
        self,
        *,
        has_review_required: bool | None = None,
        source: TextSource | None = None,
        status: TextStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TextWithStats]:
        items = sorted(
            self._items.values(), key=lambda t: (t.created_at, t.id), reverse=True
        )
        if source is not None:
            items = [t for t in items if t.source is source]
        if status is not None:
            items = [t for t in items if t.status is status]

        result: list[TextWithStats] = []
        for t in items:
            actions_count, needs_review_count = self._stats_for(t.id)
            if has_review_required is True and needs_review_count == 0:
                continue
            if has_review_required is False and needs_review_count > 0:
                continue
            result.append(
                TextWithStats(
                    text=t,
                    actions_count=actions_count,
                    needs_review_count=needs_review_count,
                )
            )

        return result[offset : offset + limit]

    def _stats_for(self, text_id: int) -> tuple[int, int]:
        provider = self._stats_provider
        if provider is None:
            return 0, 0
        return provider(text_id)

    async def update_status(
        self, text_id: int, status: TextStatus
    ) -> TextEntity | None:
        current = self._items.get(text_id)
        if current is None:
            return None
        updated = TextEntity(
            id=current.id,
            source=current.source,
            raw_text=current.raw_text,
            status=status,
            created_at=current.created_at,
            updated_at=datetime.now(tz=UTC),
        )
        self._items[text_id] = updated
        return updated

    async def delete(self, text_id: int) -> bool:
        return self._items.pop(text_id, None) is not None

    async def count(self) -> int:
        return len(self._items)