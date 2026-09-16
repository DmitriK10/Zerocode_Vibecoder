"""Shared test fixtures.

* ``_clean_env`` — removes environment variables that could leak into
  :class:`Settings` construction.
* ``engine`` / ``session`` — in-memory async SQLite engine with all tables
  created and ``PRAGMA foreign_keys=ON`` enforced on every connection.
* ``fake_*_repo`` — Fake repositories bound to the current test.
* ``fake_llm`` — deterministic fake LLM client.
* ``app`` — FastAPI app with all repos/LLM overridden with fakes.
* ``client`` — ``httpx.AsyncClient`` talking to the app via ASGI transport.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — register models on Base.metadata
from app.api.deps import (
    get_action_repository,
    get_audit_repository,
    get_llm_client,
    get_text_repository,
)
from app.config import Settings
from app.db.base import Base
from app.db.session import get_session
from app.llm.fake_client import FakeLLMClient
from app.main import create_app
from app.repositories.fake import (
    FakeActionRepository,
    FakeAuditRepository,
    FakeTextRepository,
)

_ENV_PREFIXES: tuple[str, ...] = (
    "APP_",
    "DB_",
    "DATABASE_",
    "LLM_",
    "TEXT_",
    "AUDIT_",
    "RATE_LIMIT_",
    "API_AUTH_",
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ.keys()):
        if key.startswith(_ENV_PREFIXES):
            monkeypatch.delenv(key, raising=False)


# ---------------------------------------------------------------------------
# In-memory DB
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(eng.sync_engine, "connect")
    def _enable_sqlite_fk(dbapi_conn: object, _record: object) -> None:
        cursor = dbapi_conn.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        await eng.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as s:
        yield s


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_text_repo() -> FakeTextRepository:
    return FakeTextRepository()


@pytest.fixture
def fake_action_repo() -> FakeActionRepository:
    return FakeActionRepository()


@pytest.fixture
def fake_audit_repo() -> FakeAuditRepository:
    return FakeAuditRepository()


@pytest.fixture
def fake_llm() -> FakeLLMClient:
    return FakeLLMClient()


def _make_stats_provider(action_repo: FakeActionRepository):
    """Wire FakeTextRepository list_with_stats to count from actions."""

    def provider(text_id: int) -> tuple[int, int]:
        items = [
            a for a in action_repo.all_entities() if a.text_id == text_id
        ]
        return len(items), sum(1 for a in items if a.needs_review)

    return provider


# ---------------------------------------------------------------------------
# FastAPI app + client with fakes
# ---------------------------------------------------------------------------


@pytest.fixture
def api_settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        rate_limit_per_minute=10_000,
        text_min_length=10,
        text_max_length=20_000,
    )


@pytest.fixture
def app(
    api_settings: Settings,
    engine: AsyncEngine,
    fake_text_repo: FakeTextRepository,
    fake_action_repo: FakeActionRepository,
    fake_audit_repo: FakeAuditRepository,
    fake_llm: FakeLLMClient,
) -> FastAPI:
    fake_text_repo.set_stats_provider(_make_stats_provider(fake_action_repo))

    application = create_app(api_settings)

    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with factory() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    application.dependency_overrides[get_session] = _override_session
    application.dependency_overrides[get_text_repository] = lambda: fake_text_repo
    application.dependency_overrides[get_action_repository] = lambda: fake_action_repo
    application.dependency_overrides[get_audit_repository] = lambda: fake_audit_repo
    application.dependency_overrides[get_llm_client] = lambda: fake_llm

    return application


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as c:
        yield c