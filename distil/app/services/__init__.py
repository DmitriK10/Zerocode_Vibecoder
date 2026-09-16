"""Service layer.

Public API:
* ``ValidationService`` — input validation and prompt-injection detection.
* ``AuditService`` — records every meaningful operation in ``audit_runs``.
* ``TextService`` — lifecycle of raw texts.
* ``ActionService`` — read access to extracted actions.
* ``ExtractionService`` — orchestration: text -> LLM -> parse -> save -> audit.
* ``ReviewService`` — manual review workflow (confirm / edit / reject / delete).
"""

from app.services.action_service import ActionService
from app.services.audit_service import AuditService
from app.services.exceptions import (
    ExtractionError,
    NotFoundError,
    ServiceError,
    ValidationError,
)
from app.services.extraction_service import ExtractionResult, ExtractionService
from app.services.review_service import ReviewService
from app.services.text_service import TextService
from app.services.validation_service import ValidationOutcome, ValidationService

__all__ = [
    "ActionService",
    "AuditService",
    "ExtractionError",
    "ExtractionResult",
    "ExtractionService",
    "NotFoundError",
    "ReviewService",
    "ServiceError",
    "TextService",
    "ValidationError",
    "ValidationOutcome",
    "ValidationService",
]