"""Tests for HTMX endpoints that mutate actions and texts."""

from __future__ import annotations

import json

import httpx

from app.llm.fake_client import FakeLLMClient

SOURCE_TEXT = "Иван, привет! Нужно до пятницы подготовить отчёт по продажам."

_ITEM = {
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


async def _seed_action(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> tuple[int, int]:
    fake_llm.enqueue(json.dumps({"actions": [_ITEM]}))
    create = await client.post(
        "/web/texts",
        data={"source": "email", "raw_text": SOURCE_TEXT},
        follow_redirects=False,
    )
    text_id = int(create.headers["location"].split("/")[2].split("?")[0])
    extract = await client.post(f"/web/texts/{text_id}/extract", data={"force": "false"})
    assert extract.status_code == 200
    assert "action-" in extract.text
    action_id = int(extract.text.split('id="action-')[1].split('"')[0])
    return text_id, action_id


async def test_extract_returns_html_partial(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    """Extract endpoint returns an HTMX-swappable fragment with the action."""
    fake_llm.enqueue(json.dumps({"actions": [_ITEM]}))
    create = await client.post(
        "/web/texts",
        data={"source": "email", "raw_text": SOURCE_TEXT},
        follow_redirects=False,
    )
    text_id = int(create.headers["location"].split("/")[2].split("?")[0])

    response = await client.post(
        f"/web/texts/{text_id}/extract", data={"force": "false"}
    )
    assert response.status_code == 200
    assert 'id="actions-section"' in response.text
    assert "Подготовить отчёт" in response.text
    assert 'id="action-' in response.text


async def test_action_row_endpoint(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    _, action_id = await _seed_action(client, fake_llm)
    response = await client.get(f"/web/actions/{action_id}/row")
    assert response.status_code == 200
    assert f'id="action-{action_id}"' in response.text


async def test_action_edit_row_endpoint(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    _, action_id = await _seed_action(client, fake_llm)
    response = await client.get(f"/web/actions/{action_id}/edit")
    assert response.status_code == 200
    assert "Сохранить" in response.text


async def test_confirm_action_via_htmx(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    _, action_id = await _seed_action(client, fake_llm)
    response = await client.post(f"/web/actions/{action_id}/confirm")
    assert response.status_code == 200
    assert "confirmed" in response.text
    assert f'id="action-{action_id}"' in response.text


async def test_reject_action_via_htmx(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    _, action_id = await _seed_action(client, fake_llm)
    response = await client.post(f"/web/actions/{action_id}/reject")
    assert response.status_code == 200
    assert "rejected" in response.text


async def test_save_action_via_htmx(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    _, action_id = await _seed_action(client, fake_llm)
    response = await client.patch(
        f"/web/actions/{action_id}",
        data={
            "title": "Обновлённый заголовок",
            "assignee": "Ivan",
            "due_date": "2026-09-19",
            "priority": "high",
        },
    )
    assert response.status_code == 200
    assert "Обновлённый заголовок" in response.text
    assert "Ivan" in response.text
    assert "2026-09-19" in response.text


async def test_save_action_with_bad_date_returns_error(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    _, action_id = await _seed_action(client, fake_llm)
    response = await client.patch(
        f"/web/actions/{action_id}",
        data={
            "title": "X",
            "assignee": "",
            "due_date": "not-a-date",
            "priority": "medium",
        },
    )
    assert response.status_code == 200
    assert "YYYY-MM-DD" in response.text


async def test_delete_action_via_htmx(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    _, action_id = await _seed_action(client, fake_llm)
    response = await client.delete(f"/web/actions/{action_id}")
    assert response.status_code == 200
    assert response.text.strip() == ""

    response = await client.get(f"/web/actions/{action_id}/row")
    assert response.status_code == 404


async def test_delete_text_via_htmx_returns_hx_redirect(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    text_id, _ = await _seed_action(client, fake_llm)
    response = await client.delete(f"/web/texts/{text_id}")
    assert response.status_code == 200
    assert response.headers.get("HX-Redirect") == "/"


async def test_action_row_missing_returns_404(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/web/actions/9999/row")
    assert response.status_code == 404