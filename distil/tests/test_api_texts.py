"""Tests for the ``/api/texts`` endpoints."""

from __future__ import annotations

import httpx
import pytest

from app.repositories.fake import FakeActionRepository, FakeTextRepository


async def test_create_text_returns_201(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/texts",
        json={
            "source": "email",
            "raw_text": "Hello world, this is a valid long text.",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["source"] == "email"
    assert data["status"] == "new"
    assert data["raw_text"] == "Hello world, this is a valid long text."
    assert "created_at" in data


async def test_create_text_too_short_returns_422(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/texts", json={"source": "email", "raw_text": "hi"}
    )
    assert response.status_code == 422


async def test_create_text_invalid_source_returns_422(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/texts",
        json={"source": "telegram", "raw_text": "A long enough raw text."},
    )
    assert response.status_code == 422


async def test_list_texts_returns_summaries(
    client: httpx.AsyncClient,
) -> None:
    await client.post(
        "/api/texts",
        json={"source": "email", "raw_text": "First long enough text."},
    )
    await client.post(
        "/api/texts",
        json={"source": "note", "raw_text": "Second long enough text."},
    )
    response = await client.get("/api/texts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all("actions_count" in item for item in data)
    assert all("raw_text" not in item for item in data)


async def test_list_texts_filters_by_source(
    client: httpx.AsyncClient,
) -> None:
    await client.post(
        "/api/texts",
        json={"source": "email", "raw_text": "First long enough text."},
    )
    await client.post(
        "/api/texts",
        json={"source": "note", "raw_text": "Second long enough text."},
    )
    response = await client.get("/api/texts", params={"source": "email"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["source"] == "email"


async def test_list_texts_filters_by_has_review_required(
    client: httpx.AsyncClient,
    fake_text_repo: FakeTextRepository,
    fake_action_repo: FakeActionRepository,
) -> None:
    from app.domain.action import ActionCreate
    from app.domain.enums import Priority, ReviewSeverity

    # text 1: no actions at all
    t1 = (await client.post(
        "/api/texts",
        json={"source": "email", "raw_text": "Text with no actions."},
    )).json()

    # text 2: has an action flagged needs_review
    t2 = (await client.post(
        "/api/texts",
        json={"source": "note", "raw_text": "Text with review action."},
    )).json()

    await fake_action_repo.create_many(
        text_id=t2["id"],
        actions=[
            ActionCreate(
                title="Review me",
                assignee=None,
                due_date=None,
                due_date_raw=None,
                priority=Priority.MEDIUM,
                source_quote="Text",
                confidence=0.5,
                needs_review=True,
                review_reason="Не указан исполнитель",
                review_severity=ReviewSeverity.SOFT,
            )
        ],
    )

    response = await client.get(
        "/api/texts", params={"has_review_required": "true"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == t2["id"]
    assert data[0]["needs_review_count"] == 1

    _ = (t1, fake_text_repo)  # silence unused warnings in some linters


async def test_get_text_detail_returns_actions(
    client: httpx.AsyncClient,
) -> None:
    created = (
        await client.post(
            "/api/texts",
            json={"source": "email", "raw_text": "Some long enough text."},
        )
    ).json()
    response = await client.get(f"/api/texts/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["text"]["id"] == created["id"]
    assert data["actions"] == []


async def test_get_missing_text_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/texts/9999")
    assert response.status_code == 404
    body = response.json()
    assert body["error"] == "not_found"


async def test_delete_text_returns_204(client: httpx.AsyncClient) -> None:
    created = (
        await client.post(
            "/api/texts",
            json={"source": "email", "raw_text": "Some long enough text."},
        )
    ).json()
    response = await client.delete(f"/api/texts/{created['id']}")
    assert response.status_code == 204

    response = await client.get(f"/api/texts/{created['id']}")
    assert response.status_code == 404


async def test_delete_missing_text_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.delete("/api/texts/9999")
    assert response.status_code == 404


@pytest.mark.parametrize("limit,offset", [(0, 0), (500, 0), (10, -1)])
async def test_list_texts_rejects_invalid_pagination(
    client: httpx.AsyncClient, limit: int, offset: int
) -> None:
    response = await client.get(
        "/api/texts", params={"limit": limit, "offset": offset}
    )
    assert response.status_code == 422