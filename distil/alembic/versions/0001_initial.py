"""Initial schema: texts, actions, audit_runs.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-13

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------------- texts
    op.create_table(
        "texts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="new",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "source IN ('email','meeting','note')",
            name="ck_texts_source_valid",
        ),
        sa.CheckConstraint(
            "status IN ('new','extracted','failed')",
            name="ck_texts_status_valid",
        ),
        sa.CheckConstraint(
            "length(raw_text) >= 10 AND length(raw_text) <= 20000",
            name="ck_texts_raw_text_length",
        ),
    )
    op.create_index("ix_texts_source", "texts", ["source"])
    op.create_index("ix_texts_status", "texts", ["status"])

    # -------------------------------------------------------------- actions
    op.create_table(
        "actions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "text_id",
            sa.BigInteger(),
            sa.ForeignKey("texts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("assignee", sa.String(length=120), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("due_date_raw", sa.String(length=120), nullable=True),
        sa.Column(
            "priority",
            sa.String(length=10),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("source_quote", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "needs_review",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.Column("review_severity", sa.String(length=10), nullable=True),
        sa.Column(
            "review_status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "priority IN ('low','medium','high')",
            name="ck_actions_priority_valid",
        ),
        sa.CheckConstraint(
            "review_status IN ('pending','confirmed','edited','rejected')",
            name="ck_actions_review_status_valid",
        ),
        sa.CheckConstraint(
            "review_severity IS NULL OR review_severity IN ('soft','critical')",
            name="ck_actions_review_severity_valid",
        ),
        sa.CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="ck_actions_confidence_range",
        ),
    )
    op.create_index("ix_actions_text_id", "actions", ["text_id"])
    op.create_index("ix_actions_needs_review", "actions", ["needs_review"])
    op.create_index("ix_actions_review_status", "actions", ["review_status"])

    # ------------------------------------------------------------ audit_runs
    op.create_table(
        "audit_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column(
            "input",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "output",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "needs_review_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('ok','error')",
            name="ck_audit_runs_status_valid",
        ),
        sa.CheckConstraint(
            "duration_ms >= 0",
            name="ck_audit_runs_duration_non_negative",
        ),
        sa.CheckConstraint(
            "needs_review_count >= 0",
            name="ck_audit_runs_review_count_non_negative",
        ),
    )
    op.create_index("ix_audit_runs_action", "audit_runs", ["action"])
    op.create_index("ix_audit_runs_status", "audit_runs", ["status"])
    op.create_index("ix_audit_runs_created_at", "audit_runs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_runs_created_at", table_name="audit_runs")
    op.drop_index("ix_audit_runs_status", table_name="audit_runs")
    op.drop_index("ix_audit_runs_action", table_name="audit_runs")
    op.drop_table("audit_runs")

    op.drop_index("ix_actions_review_status", table_name="actions")
    op.drop_index("ix_actions_needs_review", table_name="actions")
    op.drop_index("ix_actions_text_id", table_name="actions")
    op.drop_table("actions")

    op.drop_index("ix_texts_status", table_name="texts")
    op.drop_index("ix_texts_source", table_name="texts")
    op.drop_table("texts")