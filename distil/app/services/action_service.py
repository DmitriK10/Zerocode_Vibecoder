"""ActionService — read access to extracted actions.

Write operations on actions (manual review) live in :class:`ReviewService`
because they carry review semantics and require their own audit entries.
This service only reads.
"""

from __future__ import annotations

from app.domain.action import ActionEntity
from app.repositories.protocols import ActionRepositoryProtocol


class ActionService:
    """Read-only access to extracted actions."""

    def __init__(self, repository: ActionRepositoryProtocol) -> None:
        self._repo = repository

    async def get(self, action_id: int) -> ActionEntity | None:
        """Return an action by id, or ``None``."""
        return await self._repo.get_by_id(action_id)

    async def list_by_text(self, text_id: int) -> list[ActionEntity]:
        """Return all actions attached to a text, ordered by id."""
        return await self._repo.list_by_text(text_id)

    async def count_by_text(self, text_id: int) -> tuple[int, int]:
        """Return ``(total, needs_review)`` counts for a text."""
        return await self._repo.count_by_text(text_id)