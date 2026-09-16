"""Domain layer.

Contains:
* Enumerations used across the system.
* Immutable DTOs (domain entities) that services operate on.

The domain layer has zero dependencies on SQLAlchemy, FastAPI or OpenAI —
this is what allows services to be truly decoupled from infrastructure
(Dependency Inversion Principle).
"""

from app.domain.action import ActionCreate, ActionEntity
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
from app.domain.text import TextEntity, TextWithStats

__all__ = [
    "ActionCreate",
    "ActionEntity",
    "AuditAction",
    "AuditRunEntity",
    "AuditStatus",
    "Priority",
    "ReviewSeverity",
    "ReviewStatus",
    "TextEntity",
    "TextSource",
    "TextStatus",
    "TextWithStats",
]