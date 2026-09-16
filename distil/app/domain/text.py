"""Domain entities for texts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.enums import TextSource, TextStatus


@dataclass(frozen=True, slots=True)
class TextEntity:
    """A raw text submitted for extraction."""

    id: int
    source: TextSource
    raw_text: str
    status: TextStatus
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class TextWithStats:
    """A text together with aggregate statistics on its actions.

    Used by the showcase list to display ``actions_count`` and
    ``needs_review_count`` without N+1 queries.
    """

    text: TextEntity
    actions_count: int
    needs_review_count: int