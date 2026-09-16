"""``audit_runs`` — one row per meaningful operation in the system."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Integer,
    String,
    func,
)
from sqlalchemy import (
    Text as SAText,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import BigIntType, JSONType


class AuditRun(Base):
    """Audit record for a single operation.

    ``status`` is strictly ``ok`` | ``error`` — this is an *operational*
    status. Business-level review state lives on :class:`Action` and is
    only summarised here via ``needs_review_count``.
    """

    __tablename__ = "audit_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ok','error')",
            name="ck_audit_runs_status_valid",
        ),
        CheckConstraint(
            "duration_ms >= 0",
            name="ck_audit_runs_duration_non_negative",
        ),
        CheckConstraint(
            "needs_review_count >= 0",
            name="ck_audit_runs_review_count_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigIntType, primary_key=True, autoincrement=True
    )
    action: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    input_payload: Mapped[dict[str, object] | None] = mapped_column(
        "input", JSONType, nullable=True
    )
    output_payload: Mapped[dict[str, object] | None] = mapped_column(
        "output", JSONType, nullable=True
    )
    needs_review_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    error: Mapped[str | None] = mapped_column(SAText, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<AuditRun id={self.id} action={self.action} "
            f"status={self.status} duration_ms={self.duration_ms}>"
        )