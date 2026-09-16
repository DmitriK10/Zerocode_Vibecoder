"""Tests for CSV/JSON export endpoints."""

from __future__ import annotations

import csv
import io
import json

import httpx

from app.llm.fake_client import FakeLLMClient

SOURCE_TEXT = "Иван, привет! Нужно до пятницы подготовить отчёт по продажам."

_ITEM = {
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


async def _seed(client: httpx.AsyncClient, fake_llm: FakeLLMClient) -> None:
    fake_llm.enqueue(json.dumps({"actions": [_ITEM]}))
    create = await client.post(
        "/web/texts",
        data={"source": "email", "raw_text": SOURCE_TEXT},
        follow_redirects=False,
    )
    text_id = int(create.headers["location"].split("/")[2].split("?")[0])
    await client.post(f"/web/texts/{text_id}/extract", data={"force": "false"})


async def test_actions_json_export(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    await _seed(client, fake_llm)
    response = await client.get("/export/actions.json")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Подготовить отчёт"
    assert data[0]["assignee"] == "Иван"
    assert data[0]["priority"] == "high"


async def test_actions_csv_export(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    await _seed(client, fake_llm)
    response = await client.get("/export/actions.csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]

    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["title"] == "Подготовить отчёт"
    assert rows[0]["priority"] == "high"


async def test_texts_json_export(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    await _seed(client, fake_llm)
    response = await client.get("/export/texts.json")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["source"] == "email"
    assert data[0]["actions_count"] == 1


async def test_texts_csv_export(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    await _seed(client, fake_llm)
    response = await client.get("/export/texts.csv")
    assert response.status_code == 200
    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["source"] == "email"
    assert rows[0]["actions_count"] == "1"


async def test_actions_export_filters_by_review_required(
    client: httpx.AsyncClient, fake_llm: FakeLLMClient
) -> None:
    await _seed(client, fake_llm)
    response = await client.get(
        "/export/actions.json", params={"has_review_required": "true"}
    )
    assert response.status_code == 200
    assert response.json() == []