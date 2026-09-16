"""``actions`` — extracted action items with review state."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    String,
    false,
    func,
)
from sqlalchemy import (
    Text as SAText,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import BigIntType

if TYPE_CHECKING:
    from app.models.text import Text


class Action(Base):
    """A single action extracted from a :class:`Text`."""

    __tablename__ = "actions"
    __table_args__ = (
        CheckConstraint(
            "priority IN ('low','medium','high')",
            name="ck_actions_priority_valid",
        ),
        CheckConstraint(
            "review_status IN ('pending','confirmed','edited','rejected')",
            name="ck_actions_review_status_valid",
        ),
        CheckConstraint(
            "review_severity IS NULL OR review_severity IN ('soft','critical')",
            name="ck_actions_review_severity_valid",
        ),
        CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="ck_actions_confidence_range",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigIntType, primary_key=True, autoincrement=True
    )
    text_id: Mapped[int] = mapped_column(
        BigIntType,
        ForeignKey("texts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    assignee: Mapped[str | None] = mapped_column(String(120), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date_raw: Mapped[str | None] = mapped_column(String(120), nullable=True)
    priority: Mapped[str] = mapped_column(
        String(10), nullable=False, default="medium", server_default="medium"
    )
    source_quote: Mapped[str] = mapped_column(SAText, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    needs_review: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
        index=True,
    )
    review_reason: Mapped[str | None] = mapped_column(SAText, nullable=True)
    review_severity: Mapped[str | None] = mapped_column(String(10), nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    text: Mapped[Text] = relationship(back_populates="actions")

    def __repr__(self) -> str:
        return (
            f"<Action id={self.id} text_id={self.text_id} "
            f"priority={self.priority} needs_review={self.needs_review}>"
        )