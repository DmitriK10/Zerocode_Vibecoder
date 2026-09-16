"""Tests for ``GET /health``."""

from __future__ import annotations

import httpx


async def test_health_returns_ok(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"
    assert data["app_name"] == "distil"
    assert data["llm_model"] == "gpt-4o-mini"
    assert "version" in data
    assert data["env"] == "test"