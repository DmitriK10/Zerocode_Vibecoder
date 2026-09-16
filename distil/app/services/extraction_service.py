"""ExtractionService — the core orchestration of the product.

Flow:
    text_id -> load text -> delete stale actions -> call LLM
            -> parse & validate -> save actions -> update text status
            -> write audit entry.

Re-extraction
-------------
Each call to :meth:`extract` removes any previously extracted actions
for the text before saving the new ones. This makes the operation
idempotent: pressing "Extract" repeatedly always yields a single fresh
set of actions instead of accumulating duplicates.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.action import ActionEntity
from app.domain.enums import AuditAction, TextStatus
from app.llm.exceptions import LLMError, LLMParseError
from app.llm.parser import parse_llm_response
from app.llm.prompts import detect_prompt_injection
from app.llm.protocol import LLMClientProtocol, LLMRequest
from app.logging_config import get_logger
from app.repositories.protocols import (
    ActionRepositoryProtocol,
    TextRepositoryProtocol,
)
from app.services.audit_service import AuditService
from app.services.exceptions import ExtractionError, NotFoundError
from app.services.timing import elapsed_ms, now_monotonic

logger = get_logger("distil.services.extraction")


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Result of a successful extraction run."""

    text_id: int
    actions: list[ActionEntity]
    needs_review_count: int
    duration_ms: int
    injection_detected: bool


class ExtractionService:
    """Orchestrates text → LLM → parse → save → audit."""

    def __init__(
        self,
        *,
        text_repository: TextRepositoryProtocol,
        action_repository: ActionRepositoryProtocol,
        llm_client: LLMClientProtocol,
        audit: AuditService,
    ) -> None:
        self._texts = text_repository
        self._actions = action_repository
        self._llm = llm_client
        self._audit = audit

    async def extract(
        self, text_id: int, *, force: bool = False
    ) -> ExtractionResult:
        """Run the extraction pipeline for ``text_id``.

        Always overwrites any previously extracted actions for the text,
        making the operation idempotent.

        Raises:
            NotFoundError: if the text does not exist.
            ExtractionError: if the LLM call or the JSON parsing fails.
        """
        started = now_monotonic()

        text = await self._texts.get_by_id(text_id)
        if text is None:
            await self._audit.record_error(
                action=AuditAction.EXTRACT_ACTIONS,
                duration_ms=elapsed_ms(started),
                error=f"Text {text_id} not found",
                input_payload={"text_id": text_id},
            )
            raise NotFoundError(f"Text {text_id} not found")

        # Remove stale actions so re-extraction produces a fresh set
        # rather than a growing pile of duplicates.
        deleted = await self._actions.delete_by_text(text_id)
        if deleted > 0:
            logger.info(
                "extraction_cleanup",
                text_id=text_id,
                deleted=deleted,
            )

        # Informational: record prompt-injection verdict in the audit trail.
        injection = detect_prompt_injection(text.raw_text)

        # --- LLM call ------------------------------------------------------
        try:
            response = await self._llm.extract_actions(
                LLMRequest(text=text.raw_text)
            )
        except LLMError as exc:
            await self._audit.record_error(
                action=AuditAction.EXTRACT_ACTIONS,
                duration_ms=elapsed_ms(started),
                error=f"LLM error: {exc}",
                input_payload={"text_id": text_id},
            )
            await self._texts.update_status(text_id, TextStatus.FAILED)
            raise ExtractionError(
                f"LLM call failed: {exc}", reason="llm_error"
            ) from exc

        # --- Parse & validate ---------------------------------------------
        try:
            create_items = parse_llm_response(response.raw_json, text.raw_text)
        except LLMParseError as exc:
            await self._audit.record_error(
                action=AuditAction.EXTRACT_ACTIONS,
                duration_ms=elapsed_ms(started),
                error=f"Parse error: {exc}",
                input_payload={"text_id": text_id},
            )
            await self._texts.update_status(text_id, TextStatus.FAILED)
            raise ExtractionError(
                f"LLM response could not be parsed: {exc}",
                reason="parse_error",
            ) from exc

        # --- Persist actions ----------------------------------------------
        saved = await self._actions.create_many(
            text_id=text_id, actions=create_items
        )
        await self._texts.update_status(text_id, TextStatus.EXTRACTED)

        needs_review_count = sum(1 for a in saved if a.needs_review)
        duration = elapsed_ms(started)

        await self._audit.record_success(
            action=AuditAction.EXTRACT_ACTIONS,
            duration_ms=duration,
            input_payload={
                "text_id": text_id,
                "injection_detected": injection.detected,
                "injection_patterns": list(injection.matched_patterns),
                "replaced_actions": deleted,
            },
            output_payload={
                "actions_count": len(saved),
                "needs_review_count": needs_review_count,
            },
            needs_review_count=needs_review_count,
        )

        return ExtractionResult(
            text_id=text_id,
            actions=saved,
            needs_review_count=needs_review_count,
            duration_ms=duration,
            injection_detected=injection.detected,
        )