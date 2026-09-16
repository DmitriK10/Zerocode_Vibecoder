"""Mappers between ORM models and domain entities.

Mapping is intentionally kept in one place so the rest of the code never
has to know about SQLAlchemy model structure.
"""

from __future__ import annotations

from app.domain.action import ActionEntity
from app.domain.audit import AuditRunEntity
from app.domain.enums import (
    AuditAction,
    AuditStatus,
    Priority,
    ReviewSeverity,
    ReviewStatus,
    TextSource,
    TextStatus,
)
from app.domain.text import TextEntity
from app.models.action import Action as ActionORM
from app.models.audit import AuditRun as AuditRunORM
from app.models.text import Text as TextORM


def text_to_entity(orm: TextORM) -> TextEntity:
    return TextEntity(
        id=orm.id,
        source=TextSource(orm.source),
        raw_text=orm.raw_text,
        status=TextStatus(orm.status),
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def action_to_entity(orm: ActionORM) -> ActionEntity:
    severity = ReviewSeverity(orm.review_severity) if orm.review_severity else None
    return ActionEntity(
        id=orm.id,
        text_id=orm.text_id,
        title=orm.title,
        assignee=orm.assignee,
        due_date=orm.due_date,
        due_date_raw=orm.due_date_raw,
        priority=Priority(orm.priority),
        source_quote=orm.source_quote,
        confidence=orm.confidence,
        needs_review=orm.needs_review,
        review_reason=orm.review_reason,
        review_severity=severity,
        review_status=ReviewStatus(orm.review_status),
        reviewed_at=orm.reviewed_at,
        reviewed_by=orm.reviewed_by,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def audit_to_entity(orm: AuditRunORM) -> AuditRunEntity:
    return AuditRunEntity(
        id=orm.id,
        action=AuditAction(orm.action),
        status=AuditStatus(orm.status),
        input_payload=orm.input_payload,
        output_payload=orm.output_payload,
        needs_review_count=orm.needs_review_count,
        error=orm.error,
        duration_ms=orm.duration_ms,
        created_at=orm.created_at,
    )