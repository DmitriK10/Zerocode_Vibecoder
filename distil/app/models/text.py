"""``texts`` — raw inputs submitted for extraction."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    String,
    func,
)
from sqlalchemy import (
    Text as SAText,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import BigIntType

if TYPE_CHECKING:
    from app.models.action import Action


class Text(Base):
    """A raw text submitted by the user (email, meeting transcript, note)."""

    __tablename__ = "texts"
    __table_args__ = (
        CheckConstraint(
            "source IN ('email','meeting','note')",
            name="ck_texts_source_valid",
        ),
        CheckConstraint(
            "status IN ('new','extracted','failed')",
            name="ck_texts_status_valid",
        ),
        CheckConstraint(
            "length(raw_text) >= 10 AND length(raw_text) <= 20000",
            name="ck_texts_raw_text_length",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigIntType, primary_key=True, autoincrement=True
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    raw_text: Mapped[str] = mapped_column(SAText, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="new",
        server_default="new",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    actions: Mapped[list[Action]] = relationship(
        back_populates="text",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Text id={self.id} source={self.source} status={self.status}>"