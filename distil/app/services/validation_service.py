"""Input validation and prompt-injection detection.

This service is intentionally narrow: it only *checks* inputs and returns
verdicts. It never touches the database and never calls the LLM. This keeps
it trivially testable and reusable from both the API and CLI layers.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings
from app.domain.enums import TextSource
from app.llm.prompts import InjectionVerdict, detect_prompt_injection
from app.services.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class ValidationOutcome:
    """Result of validating a single text submission."""

    injection: InjectionVerdict


class ValidationService:
    """Validates text submissions and scans them for prompt injection."""

    def __init__(self, settings: Settings) -> None:
        self._min_length = settings.text_min_length
        self._max_length = settings.text_max_length

    def validate_text_input(
        self,
        *,
        source: TextSource,
        raw_text: str,
    ) -> ValidationOutcome:
        """Validate a text submission.

        Raises:
            ValidationError: if any input rule is violated.

        Returns:
            A :class:`ValidationOutcome` carrying the prompt-injection
            verdict (informational; services decide how to react).
        """
        if not isinstance(source, TextSource):
            raise ValidationError(f"Unknown source: {source!r}")

        if raw_text is None:
            raise ValidationError("raw_text must not be None")

        if not raw_text.strip():
            raise ValidationError("raw_text must not be empty")

        length = len(raw_text)
        if length < self._min_length:
            raise ValidationError(
                f"raw_text is too short: {length} < {self._min_length}"
            )
        if length > self._max_length:
            raise ValidationError(
                f"raw_text is too long: {length} > {self._max_length}"
            )

        injection = detect_prompt_injection(raw_text)
        return ValidationOutcome(injection=injection)