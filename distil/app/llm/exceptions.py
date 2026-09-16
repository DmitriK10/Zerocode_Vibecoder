"""Typed exceptions raised by the LLM layer.

Splitting ``LLMError`` into subclasses lets the service layer react
differently to configuration mistakes, upstream failures and parse errors.
"""

from __future__ import annotations


class LLMError(Exception):
    """Base class for every error raised by the LLM layer."""


class LLMConfigError(LLMError):
    """Raised when the LLM client is misconfigured (e.g. disallowed model)."""


class LLMResponseError(LLMError):
    """Raised when the upstream LLM returned an unusable response envelope.

    Example: ``choices`` is empty or ``message.content`` is ``None``.
    """


class LLMParseError(LLMError):
    """Raised when the raw LLM string cannot be parsed or validated.

    Carries the original raw payload for audit logging.
    """

    def __init__(self, message: str, *, raw_payload: str | None = None) -> None:
        super().__init__(message)
        self.raw_payload = raw_payload