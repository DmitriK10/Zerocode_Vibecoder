"""TextService — lifecycle of raw texts.

Responsibilities:
* Validate input via :class:`ValidationService` before persisting.
* Persist texts via :class:`TextRepositoryProtocol`.
* Record every mutation in the audit log via :class:`AuditService`.

Error handling
--------------
* :class:`ValidationError` is caught narrowly (it is the only exception
  ``validate_text_input`` raises) and audited as an operator-visible
  rejection.
* Repository failures are caught by a broad ``except Exception`` because
  the service depends on an abstract :class:`TextRepositoryProtocol` and
  cannot know the concrete exception hierarchy. In exchange, the full
  traceback goes to the structured log via ``logger.exception`` and the
  audit entry keeps only the exception *type* (never the message), so
  bugs remain visible in logs while the audit trail stays clean.
"""

from __future__ import annotations

from app.domain.enums import AuditAction, TextSource, TextStatus
from app.domain.text import TextEntity, TextWithStats
from app.logging_config import get_logger
from app.repositories.protocols import TextRepositoryProtocol
from app.services.audit_service import AuditService
from app.services.exceptions import ValidationError
from app.services.timing import elapsed_ms, now_monotonic
from app.services.validation_service import ValidationService

logger = get_logger("distil.services.text")


class TextService:
    """Create, read and delete raw texts with audit and validation."""

    def __init__(
        self,
        *,
        repository: TextRepositoryProtocol,
        validation: ValidationService,
        audit: AuditService,
    ) -> None:
        self._repo = repository
        self._validation = validation
        self._audit = audit

    async def create(
        self,
        *,
        source: TextSource,
        raw_text: str,
    ) -> TextEntity:
        """Validate, persist and audit a new text."""
        started = now_monotonic()

        # -- Validation --------------------------------------------------
        try:
            self._validation.validate_text_input(
                source=source, raw_text=raw_text
            )
        except ValidationError as exc:
            await self._audit.record_error(
                action=AuditAction.CREATE_TEXT,
                duration_ms=elapsed_ms(started),
                error=f"Validation failed: {exc}",
                input_payload={
                    "source": source.value,
                    "length": len(raw_text),
                },
            )
            raise

        # -- Persist -----------------------------------------------------
        try:
            entity = await self._repo.create(source=source, raw_text=raw_text)
        except Exception as exc:
            # Full traceback for developers; audit keeps only the type
            # so a bug in the repo layer cannot masquerade as a DB error
            # in the audit log.
            logger.exception(
                "text_create_repository_error",
                source=source.value,
                length=len(raw_text),
            )
            await self._audit.record_error(
                action=AuditAction.CREATE_TEXT,
                duration_ms=elapsed_ms(started),
                error=f"Repository error ({type(exc).__name__})",
                input_payload={
                    "source": source.value,
                    "length": len(raw_text),
                },
            )
            raise

        await self._audit.record_success(
            action=AuditAction.CREATE_TEXT,
            duration_ms=elapsed_ms(started),
            input_payload={"source": source.value, "length": len(raw_text)},
            output_payload={"text_id": entity.id},
        )
        return entity

    async def get(self, text_id: int) -> TextEntity | None:
        """Return a text by id, or ``None``."""
        return await self._repo.get_by_id(text_id)

    async def list_with_stats(
        self,
        *,
        has_review_required: bool | None = None,
        source: TextSource | None = None,
        status: TextStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TextWithStats]:
        """Return the showcase list (read-only; no audit)."""
        return await self._repo.list_with_stats(
            has_review_required=has_review_required,
            source=source,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def update_status(
        self,
        text_id: int,
        status: TextStatus,
    ) -> TextEntity | None:
        """Update the text status (used by :class:`ExtractionService`).

        This method intentionally does not audit: the enclosing operation
        (``extract_actions``) records its own audit entry that already
        includes the status change.
        """
        return await self._repo.update_status(text_id, status)

    async def delete(self, text_id: int) -> bool:
        """Delete a text (cascades to actions) and audit the operation."""
        started = now_monotonic()
        try:
            deleted = await self._repo.delete(text_id)
        except Exception as exc:
            logger.exception("text_delete_repository_error", text_id=text_id)
            await self._audit.record_error(
                action=AuditAction.DELETE_TEXT,
                duration_ms=elapsed_ms(started),
                error=f"Repository error ({type(exc).__name__})",
                input_payload={"text_id": text_id},
            )
            raise

        await self._audit.record_success(
            action=AuditAction.DELETE_TEXT,
            duration_ms=elapsed_ms(started),
            input_payload={"text_id": text_id},
            output_payload={"deleted": deleted},
        )
        return deleted