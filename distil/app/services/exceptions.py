"""Typed service-layer exceptions.

The API layer maps these to HTTP codes without inspecting message strings.
"""

from __future__ import annotations


class ServiceError(Exception):
    """Base class for all service-layer errors."""


class ValidationError(ServiceError):
    """Raised when input fails business-level validation rules."""


class NotFoundError(ServiceError):
    """Raised when a requested entity does not exist."""


class ConflictError(ServiceError):
    """Raised when an operation conflicts with the current entity state."""


class ExtractionError(ServiceError):
    """Raised when the LLM extraction pipeline fails.

    Wraps lower-level LLM or parse errors so the API layer has a single
    exception type to catch while still preserving the original cause.
    """

    def __init__(self, message: str, *, reason: str | None = None) -> None:
        super().__init__(message)
        self.reason = reason or message