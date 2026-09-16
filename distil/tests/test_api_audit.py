"""Tests for the ``/api/audit`` endpoints."""

from __future__ import annotations

import httpx


async def test_list_audit_after_create_text(
    client: httpx.AsyncClient,
) -> None:
    await client.post(
        "/api/texts",
        json={"source": "email", "raw_text": "A long enough raw text."},
    )
    response = await client.get("/api/audit")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["action"] == "create_text"
    assert data[0]["status"] == "ok"
    assert data[0]["duration_ms"] >= 0


async def test_audit_filter_by_status(
    client: httpx.AsyncClient,
) -> None:
    # Successful create
    await client.post(
        "/api/texts",
        json={"source": "email", "raw_text": "A long enough raw text."},
    )
    # Failed create (too short) — recorded as error
    await client.post(
        "/api/texts", json={"source": "email", "raw_text": "hi"}
    )

    response = await client.get("/api/audit", params={"status": "error"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "error"


async def test_audit_filter_by_action(
    client: httpx.AsyncClient,
) -> None:
    await client.post(
        "/api/texts",
        json={"source": "email", "raw_text": "A long enough raw text."},
    )
    response = await client.get("/api/audit", params={"action": "create_text"})
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_get_audit_by_id(
    client: httpx.AsyncClient,
) -> None:
    await client.post(
        "/api/texts",
        json={"source": "email", "raw_text": "A long enough raw text."},
    )
    listed = (await client.get("/api/audit")).json()
    audit_id = listed[0]["id"]

    response = await client.get(f"/api/audit/{audit_id}")
    assert response.status_code == 200
    assert response.json()["id"] == audit_id


async def test_get_missing_audit_returns_404(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/audit/9999")
    assert response.status_code == 404


async def test_audit_rejects_invalid_limit(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/audit", params={"limit": 0})
    assert response.status_code == 422