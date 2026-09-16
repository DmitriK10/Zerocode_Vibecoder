"""Tests for the ``/api/actions`` endpoints."""

from __future__ import annotations

import json

import httpx

from app.llm.fake_client import FakeLLMClient

SOURCE_TEXT = (
    "Иван, привет! Нужно до пятницы подготовить отчёт по продажам."
)

_ITEM_FOR_REVIEW = {
    "title": "Подготовить отчёт",
    "assignee": None,
    "due_date_raw": None,
    "due_date_iso": None,
    "priority": "medium",
    "source_quote": "Нужно до пятницы подготовить отчёт по продажам",
    "confidence": 0.9,
    "needs_review": False,
    "review_reason": None,
    "review_severity": None,
}


async def _seed_action(client: httpx.AsyncClient, fake_llm: FakeLLMClient) -> int:
    fake_llm.enqueue(json.dumps({"actions": [_ITEM_FOR_REVIEW]}))
    created = await client.post(
        "/api/texts", json={"source": "email", "raw_text": SOURCE_TEXT}
    )
    text_id = created.json()["id"]
    extract = await client.post("/api/extract", json={"text_id": text_id})
    return int(extract.json()["actions"][0]["id"])


async def test_get_action_returns_entity(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    action_id = await _seed_action(client, fake_llm)
    response = await client.get(f"/api/actions/{action_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == action_id
    assert data["review_status"] == "pending"
    assert data["needs_review"] is True
    assert data["review_severity"] == "soft"


async def test_get_missing_action_returns_404(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/actions/9999")
    assert response.status_code == 404


async def test_confirm_action_clears_review(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    action_id = await _seed_action(client, fake_llm)
    response = await client.post(f"/api/actions/{action_id}/confirm")
    assert response.status_code == 200
    data = response.json()
    assert data["review_status"] == "confirmed"
    assert data["needs_review"] is False
    assert data["reviewed_by"] == "local_user"


async def test_edit_action_applies_changes(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    action_id = await _seed_action(client, fake_llm)
    response = await client.patch(
        f"/api/actions/{action_id}",
        json={
            "title": "Исправленный заголовок",
            "assignee": "Ivan",
            "due_date": "2026-09-19",
            "priority": "high",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Исправленный заголовок"
    assert data["assignee"] == "Ivan"
    assert data["priority"] == "high"
    assert data["review_status"] == "edited"
    assert data["reviewed_at"] is not None


async def test_reject_action_marks_rejected(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    action_id = await _seed_action(client, fake_llm)
    response = await client.post(f"/api/actions/{action_id}/reject")
    assert response.status_code == 200
    data = response.json()
    assert data["review_status"] == "rejected"


async def test_delete_action_returns_204(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    action_id = await _seed_action(client, fake_llm)
    response = await client.delete(f"/api/actions/{action_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/actions/{action_id}")
    assert response.status_code == 404


async def test_confirm_missing_action_returns_404(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post("/api/actions/9999/confirm")
    assert response.status_code == 404


async def test_edit_action_rejects_unknown_priority(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    action_id = await _seed_action(client, fake_llm)
    response = await client.patch(
        f"/api/actions/{action_id}", json={"priority": "urgent"}
    )
    assert response.status_code == 422