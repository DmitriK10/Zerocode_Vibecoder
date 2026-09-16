"""Tests for HTML pages."""

from __future__ import annotations

import json

import httpx

from app.llm.fake_client import FakeLLMClient

SOURCE_TEXT = "Иван, привет! Нужно до пятницы подготовить отчёт по продажам."


async def test_index_renders_empty(client: httpx.AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert "Витрина текстов" in response.text
    assert "Пока ничего нет" in response.text


async def test_index_lists_created_text(client: httpx.AsyncClient) -> None:
    await client.post(
        "/web/texts",
        data={"source": "email", "raw_text": SOURCE_TEXT},
        follow_redirects=False,
    )
    response = await client.get("/")
    assert response.status_code == 200
    assert "email" in response.text
    assert "#1" in response.text


async def test_create_text_redirects_to_detail(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/web/texts",
        data={"source": "note", "raw_text": SOURCE_TEXT},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/texts/1")


async def test_text_detail_renders(
    client: httpx.AsyncClient,
) -> None:
    create = await client.post(
        "/web/texts",
        data={"source": "email", "raw_text": SOURCE_TEXT},
        follow_redirects=False,
    )
    location = create.headers["location"]
    response = await client.get(location)
    assert response.status_code == 200
    assert "Исходный текст" in response.text
    assert "Действий ещё нет" in response.text


async def test_text_detail_missing_returns_404(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/texts/9999")
    assert response.status_code == 404


async def test_audit_page_renders(client: httpx.AsyncClient) -> None:
    await client.post(
        "/web/texts",
        data={"source": "email", "raw_text": SOURCE_TEXT},
        follow_redirects=False,
    )
    response = await client.get("/audit")
    assert response.status_code == 200
    assert "Аудит" in response.text
    assert "create_text" in response.text


async def test_text_detail_shows_extracted_actions(
    client: httpx.AsyncClient,
    fake_llm: FakeLLMClient,
) -> None:
    fake_llm.enqueue(
        json.dumps(
            {
                "actions": [
                    {
                        "title": "Подготовить отчёт",
                        "assignee": "Иван",
                        "due_date_raw": "до пятницы",
                        "due_date_iso": "2026-09-19",
                        "priority": "high",
                        "source_quote": "Нужно до пятницы подготовить отчёт по продажам",
                        "confidence": 0.9,
                        "needs_review": False,
                        "review_reason": None,
                        "review_severity": None,
                    }
                ]
            }
        )
    )
    create = await client.post(
        "/web/texts",
        data={"source": "email", "raw_text": SOURCE_TEXT},
        follow_redirects=False,
    )
    text_id = int(create.headers["location"].split("/")[2].split("?")[0])
    await client.post(f"/web/texts/{text_id}/extract", data={"force": "false"})

    response = await client.get(f"/texts/{text_id}")
    assert response.status_code == 200
    assert "Подготовить отчёт" in response.text
    assert "Иван" in response.text