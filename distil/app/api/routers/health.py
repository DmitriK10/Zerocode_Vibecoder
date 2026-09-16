"""Health check endpoint.

Performs a shallow DB connectivity check and reports the application
identity and version. Returns 200 when the DB responds, 503 otherwise.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text as sa_text

from app import __version__
from app.api.deps import SessionDep

router = APIRouter()


@router.get("/health")
async def health(request: Request, session: SessionDep) -> JSONResponse:
    settings = request.app.state.settings
    db_status = "ok"
    db_error: str | None = None
    try:
        await session.execute(sa_text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — health must never raise
        db_status = "error"
        db_error = str(exc)

    overall = "ok" if db_status == "ok" else "degraded"
    status_code = (
        status.HTTP_200_OK if overall == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    body: dict[str, Any] = {
        "status": overall,
        "app_name": settings.app_name,
        "version": __version__,
        "env": settings.app_env,
        "db": db_status,
        "llm_model": settings.llm_model,
    }
    if db_error is not None:
        body["db_error"] = db_error

    return JSONResponse(status_code=status_code, content=body)