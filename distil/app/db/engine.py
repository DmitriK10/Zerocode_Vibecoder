"""Async SQLAlchemy engine factory.

The engine is created once per process and cached. No connections are
opened here — connections are managed by :mod:`app.db.session`.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import Settings, get_settings


def build_async_engine(settings: Settings) -> AsyncEngine:
    """Build an async engine from the given settings."""
    common: dict[str, Any] = {
        "echo": settings.db_echo,
        "pool_pre_ping": True,
        "future": True,
    }

    if settings.is_postgres:
        common.update(
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout_seconds,
        )

    return create_async_engine(settings.database_url, **common)


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Return the process-wide engine (cached)."""
    return build_async_engine(get_settings())