"""Uvicorn entry point.

Reads host/port from :class:`Settings` so that ``python run.py`` behaves
identically to the CLI in Docker and locally.
"""

from __future__ import annotations

import uvicorn

from app.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "local" and settings.app_debug,
        log_config=None,  # structlog already configured in create_app
    )


if __name__ == "__main__":
    main()