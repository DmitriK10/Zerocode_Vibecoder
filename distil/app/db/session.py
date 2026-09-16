"""Async session factory and helpers.

Exposes three entry points:

* :func:`build_session_factory` — low-level factory for custom wiring.
* :func:`get_session` — FastAPI dependency (commit/rollback on exit).
* :func:`session_scope` — async context manager for scripts and tests.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from app.db.engine import get_engine


def build_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create an ``async_sessionmaker`` bound to the given engine."""
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yield a session, commit on success."""
    factory = build_session_factory(get_engine())
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Context manager for scripts, CLI tools and tests."""
    factory = build_session_factory(get_engine())
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise