"""FastAPI application factory.

Creates a fully wired app with:
* CORS configurable via ``CORS_ORIGINS`` env variable.
* Rate limiting via slowapi (configurable, disabled for high limits).
* Registered exception handlers for all service-layer errors.
* Optional HTTP Basic Auth on the web panel (``API_AUTH_ENABLED``).
* JSON API (``app.api``) and HTML web layer (``app.web``).
* Static files mounted at ``/static``.

Side-effect policy
------------------
This factory has NO side effects on the filesystem or the environment.
In particular, ``app/static/`` is expected to exist in the repository
(a ``.gitkeep`` file guarantees it). Creating directories at runtime is
incompatible with read-only root filesystems (Kubernetes, Lambda, etc.)
and is therefore forbidden.
"""

from __future__ import annotations

from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app import __version__
from app.api import api_router
from app.api.errors import register_exception_handlers
from app.config import Settings, get_settings
from app.logging_config import configure_logging
from app.web import web_router
from app.web.auth import require_auth
from app.web.exports import router as export_router
from app.web.templating import STATIC_DIR


def _rate_limit_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle rate-limit exceptions.

    Starlette's ``add_exception_handler`` expects a callable taking
    ``Exception``; we narrow to :class:`RateLimitExceeded` via ``assert``.
    """
    assert isinstance(exc, RateLimitExceeded)
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "rate_limit_exceeded",
            "message": f"Rate limit exceeded: {exc.detail}",
        },
    )


def create_app(settings: Settings) -> FastAPI:
    """Build and configure a FastAPI application.

    The settings argument is stored on ``app.state.settings`` so that
    dependencies can pick it up without relying on a global cache.
    """
    configure_logging(
        level="DEBUG" if settings.app_debug else "INFO",
        json_output=settings.app_env != "local",
    )

    app = FastAPI(
        title="Distil API",
        version=__version__,
        description=(
            "Turn unstructured text into structured actions with "
            "honest manual review."
        ),
    )
    app.state.settings = settings

    # --- CORS (configurable via CORS_ORIGINS) ---------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Rate limiting ---------------------------------------------------
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)

    # --- Domain error handling -------------------------------------------
    register_exception_handlers(app)

    # --- Static ---------------------------------------------------------
    # The directory is expected to exist in the repo (has a .gitkeep).
    # We do NOT create it here: filesystem writes at import time break
    # in read-only environments.
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # --- Routers --------------------------------------------------------
    # Web + export require Basic Auth (when enabled). API stays open for
    # programmatic clients — flip the comment below to protect it too.
    auth_dep = [Depends(require_auth)] if settings.api_auth_enabled else []

    app.include_router(api_router)                                  # JSON API
    app.include_router(export_router, dependencies=auth_dep)        # CSV / JSON export
    app.include_router(web_router, dependencies=auth_dep)           # HTML pages + HTMX
    # app.include_router(api_router, dependencies=auth_dep)         # uncomment to protect API

    return app


app = create_app(get_settings())