"""HTTP error mapping for service-layer exceptions.

Every :class:`ServiceError` subclass is mapped to an HTTP status code.

Security note
-------------
Messages returned to the client are CURATED. Domain errors
(``ValidationError``, ``NotFoundError``, ``ConflictError``) carry
human-readable messages that are safe to expose. Infrastructure errors
(``ExtractionError`` wrapping LLM failures, generic ``ServiceError``)
are SANITIZED: the user sees a generic message, the full details go to
the structured log. This prevents leaking SQL fragments, table names or
PII to the browser.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.llm.exceptions import LLMConfigError
from app.logging_config import get_logger
from app.services.exceptions import (
    ConflictError,
    ExtractionError,
    NotFoundError,
    ServiceError,
    ValidationError,
)

logger = get_logger("distil.api.errors")

HTTP_422: int = 422


def _payload(code: str, message: str, **extra: object) -> dict[str, object]:
    body: dict[str, object] = {"error": code, "message": message}
    body.update(extra)
    return body


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all domain-level exception handlers to ``app``."""

    @app.exception_handler(ValidationError)
    async def _validation(_r: Request, exc: ValidationError) -> JSONResponse:
        # Validation messages are curated and user-facing.
        return JSONResponse(
            status_code=HTTP_422,
            content=_payload("validation_error", str(exc)),
        )

    @app.exception_handler(NotFoundError)
    async def _not_found(_r: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=_payload("not_found", str(exc)),
        )

    @app.exception_handler(ConflictError)
    async def _conflict(_r: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=_payload("conflict", str(exc)),
        )

    @app.exception_handler(ExtractionError)
    async def _extraction(_r: Request, exc: ExtractionError) -> JSONResponse:
        # Full detail goes to logs; user gets a generic message.
        logger.warning(
            "extraction_error",
            reason=exc.reason,
            detail=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=_payload(
                "extraction_error",
                "Не удалось обработать текст через языковую модель.",
                reason=exc.reason,
            ),
        )

    @app.exception_handler(LLMConfigError)
    async def _llm_config(_r: Request, exc: LLMConfigError) -> JSONResponse:
        # Config errors are operator-facing but generic enough to expose.
        logger.error("llm_config_error", detail=str(exc))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_payload(
                "llm_config_error",
                "Языковая модель временно недоступна.",
            ),
        )

    @app.exception_handler(ServiceError)
    async def _service(_r: Request, exc: ServiceError) -> JSONResponse:
        # Catch-all for any un-mapped ServiceError: log full detail, return
        # a generic message. Never leak ``str(exc)`` to the client.
        logger.exception(
            "unhandled_service_error",
            error_type=type(exc).__name__,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_payload("internal_error", "Внутренняя ошибка сервиса."),
        )