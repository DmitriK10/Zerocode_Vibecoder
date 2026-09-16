"""Domain enumerations.

Implemented as :class:`enum.StrEnum` (Python 3.11+): each member IS a
:class:`str`, so they serialise to JSON natively and compare equal to
their string values — no conversion boilerplate needed in API or DB
layers.
"""

from __future__ import annotations

from enum import StrEnum


class TextSource(StrEnum):
    EMAIL = "email"
    MEETING = "meeting"
    NOTE = "note"


class TextStatus(StrEnum):
    NEW = "new"
    EXTRACTED = "extracted"
    FAILED = "failed"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EDITED = "edited"
    REJECTED = "rejected"


class ReviewSeverity(StrEnum):
    SOFT = "soft"
    CRITICAL = "critical"


class AuditStatus(StrEnum):
    OK = "ok"
    ERROR = "error"


class AuditAction(StrEnum):
    CREATE_TEXT = "create_text"
    EXTRACT_ACTIONS = "extract_actions"
    MANUAL_REVIEW = "manual_review"
    DELETE_TEXT = "delete_text"
    IMPORT = "import"
    EXPORT = "export"