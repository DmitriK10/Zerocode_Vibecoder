"""CSV / JSON export helpers.

All serialization is explicit — no reliance on Pydantic's ``json`` mode —
so the output is stable and version-independent.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.deps import ActionServiceDep, TextServiceDep
from app.domain.action import ActionEntity
from app.domain.text import TextWithStats

router = APIRouter(prefix="/export", tags=["export"])


def _iso(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _action_to_row(a: ActionEntity) -> dict[str, Any]:
    return {
        "id": a.id,
        "text_id": a.text_id,
        "title": a.title,
        "assignee": a.assignee,
        "due_date": _iso(a.due_date),
        "due_date_raw": a.due_date_raw,
        "priority": a.priority.value,
        "source_quote": a.source_quote,
        "confidence": a.confidence,
        "needs_review": a.needs_review,
        "review_reason": a.review_reason,
        "review_severity": a.review_severity.value if a.review_severity else None,
        "review_status": a.review_status.value,
        "reviewed_at": _iso(a.reviewed_at),
        "reviewed_by": a.reviewed_by,
        "created_at": _iso(a.created_at),
        "updated_at": _iso(a.updated_at),
    }


def _text_to_row(t: TextWithStats) -> dict[str, Any]:
    return {
        "id": t.text.id,
        "source": t.text.source.value,
        "status": t.text.status.value,
        "actions_count": t.actions_count,
        "needs_review_count": t.needs_review_count,
        "created_at": _iso(t.text.created_at),
    }


def _stream_csv(rows: list[dict[str, Any]], columns: list[str]) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="export.csv"'},
    )


async def _collect_actions(
    action_service: ActionServiceDep,
    text_service: TextServiceDep,
    text_id: int | None,
    has_review_required: bool | None,
) -> list[ActionEntity]:
    """Collect actions across texts matching the filter."""
    texts = await text_service.list_with_stats(
        has_review_required=has_review_required,
        limit=10_000,
    )
    if text_id is not None:
        texts = [t for t in texts if t.text.id == text_id]

    results: list[ActionEntity] = []
    for t in texts:
        results.extend(await action_service.list_by_text(t.text.id))
    return results


@router.get("/actions.csv")
async def export_actions_csv(
    action_service: ActionServiceDep,
    text_service: TextServiceDep,
    text_id: int | None = Query(default=None),
    has_review_required: bool | None = Query(default=None),
) -> StreamingResponse:
    actions = await _collect_actions(
        action_service, text_service, text_id, has_review_required
    )
    rows = [_action_to_row(a) for a in actions]
    columns = [
        "id", "text_id", "title", "assignee", "due_date", "due_date_raw",
        "priority", "confidence", "needs_review", "review_severity",
        "review_status", "reviewed_at", "reviewed_by", "source_quote",
        "created_at", "updated_at",
    ]
    return _stream_csv(rows, columns)


@router.get("/actions.json")
async def export_actions_json(
    action_service: ActionServiceDep,
    text_service: TextServiceDep,
    text_id: int | None = Query(default=None),
    has_review_required: bool | None = Query(default=None),
) -> JSONResponse:
    actions = await _collect_actions(
        action_service, text_service, text_id, has_review_required
    )
    return JSONResponse(content=[_action_to_row(a) for a in actions])


@router.get("/texts.csv")
async def export_texts_csv(
    text_service: TextServiceDep,
    has_review_required: bool | None = Query(default=None),
) -> StreamingResponse:
    texts: Iterable[TextWithStats] = await text_service.list_with_stats(
        has_review_required=has_review_required,
        limit=10_000,
    )
    rows = [_text_to_row(t) for t in texts]
    columns = [
        "id", "source", "status", "actions_count",
        "needs_review_count", "created_at",
    ]
    return _stream_csv(rows, columns)


@router.get("/texts.json")
async def export_texts_json(
    text_service: TextServiceDep,
    has_review_required: bool | None = Query(default=None),
) -> JSONResponse:
    texts = await text_service.list_with_stats(
        has_review_required=has_review_required,
        limit=10_000,
    )
    return JSONResponse(content=[_text_to_row(t) for t in texts])