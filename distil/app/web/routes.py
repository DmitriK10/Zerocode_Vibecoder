"""HTML pages and form / HTMX endpoints."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.api.deps import (
    ActionServiceDep,
    AuditServiceDep,
    ExtractionServiceDep,
    ReviewServiceDep,
    TextServiceDep,
)
from app.domain.action import ActionEntity
from app.domain.enums import AuditStatus, Priority, TextSource
from app.logging_config import get_logger
from app.services.exceptions import NotFoundError, ValidationError
from app.web.templating import render_page, render_partial

logger = get_logger("distil.web.routes")

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    text_service: TextServiceDep,
    has_review_required: Annotated[bool | None, Query()] = None,
    msg: Annotated[str | None, Query()] = None,
) -> HTMLResponse:
    rows = await text_service.list_with_stats(
        has_review_required=has_review_required,
        limit=200,
    )
    return render_page(
        request,
        "index.html",
        rows=rows,
        has_review_required=has_review_required,
        flash=msg,
    )


@router.get("/texts/{text_id}", response_class=HTMLResponse)
async def text_detail(
    request: Request,
    text_id: int,
    text_service: TextServiceDep,
    action_service: ActionServiceDep,
    audit_service: AuditServiceDep,
    msg: Annotated[str | None, Query()] = None,
) -> HTMLResponse:
    text = await text_service.get(text_id)
    if text is None:
        raise NotFoundError(f"Text {text_id} not found")
    actions = await action_service.list_by_text(text_id)
    last_extract = next(
        (
            r
            for r in await audit_service.list_runs(limit=20)
            if r.action.value == "extract_actions"
            and r.input_payload
            and r.input_payload.get("text_id") == text_id
        ),
        None,
    )
    return render_page(
        request,
        "text_detail.html",
        text=text,
        actions=actions,
        last_extract=last_extract,
        flash=msg,
    )


@router.get("/audit", response_class=HTMLResponse)
async def audit_page(
    request: Request,
    audit_service: AuditServiceDep,
    audit_status: Annotated[AuditStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> HTMLResponse:
    runs = await audit_service.list_runs(status=audit_status, limit=limit)
    return render_page(
        request,
        "audit.html",
        runs=runs,
        audit_status=audit_status,
        limit=limit,
    )


@router.post("/web/texts", response_class=RedirectResponse)
async def web_create_text(
    text_service: TextServiceDep,
    source: Annotated[TextSource, Form()],
    raw_text: Annotated[str, Form()],
) -> RedirectResponse:
    try:
        entity = await text_service.create(source=source, raw_text=raw_text)
    except ValidationError as exc:
        logger.info("web_create_text_rejected", detail=str(exc))
        return RedirectResponse(
            url="/?msg=create_failed:validation",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception:
        logger.exception("web_create_text_failed")
        return RedirectResponse(
            url="/?msg=create_failed",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    return RedirectResponse(
        url=f"/texts/{entity.id}?msg=created",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/web/texts/{text_id}/extract", response_class=HTMLResponse)
async def web_extract(
    request: Request,
    text_id: int,
    service: ExtractionServiceDep,
    action_service: ActionServiceDep,
) -> HTMLResponse:
    try:
        await service.extract(text_id)
    except Exception:
        logger.exception("web_extract_failed", text_id=text_id)
        actions = await action_service.list_by_text(text_id)
        return render_partial(
            "partials/_actions_section.html",
            text_id=text_id,
            actions=actions,
            error="Не удалось извлечь действия. Проверьте логи.",
        )
    actions = await action_service.list_by_text(text_id)
    return render_partial(
        "partials/_actions_section.html",
        text_id=text_id,
        actions=actions,
        error=None,
    )


@router.delete("/web/texts/{text_id}", response_class=Response)
async def web_delete_text(
    text_id: int,
    text_service: TextServiceDep,
) -> Response:
    await text_service.delete(text_id)
    return Response(status_code=status.HTTP_200_OK, headers={"HX-Redirect": "/"})


async def _load_action_or_404(
    action_service: ActionServiceDep, action_id: int
) -> ActionEntity:
    action = await action_service.get(action_id)
    if action is None:
        raise NotFoundError(f"Action {action_id} not found")
    return action


@router.get("/web/actions/{action_id}/row", response_class=HTMLResponse)
async def web_action_row(
    action_id: int,
    action_service: ActionServiceDep,
) -> HTMLResponse:
    action = await _load_action_or_404(action_service, action_id)
    return render_partial("partials/_action_row.html", action=action, error=None)


@router.get("/web/actions/{action_id}/edit", response_class=HTMLResponse)
async def web_action_edit_row(
    action_id: int,
    action_service: ActionServiceDep,
) -> HTMLResponse:
    action = await _load_action_or_404(action_service, action_id)
    return render_partial("partials/_action_edit_row.html", action=action, error=None)


@router.patch("/web/actions/{action_id}", response_class=HTMLResponse)
async def web_action_save(
    action_id: int,
    service: ReviewServiceDep,
    action_service: ActionServiceDep,
    title: Annotated[str, Form()],
    assignee: Annotated[str, Form()] = "",
    due_date: Annotated[str, Form()] = "",
    priority: Annotated[str, Form()] = "medium",
) -> HTMLResponse:
    parsed_due: date | None = None
    if due_date.strip():
        try:
            parsed_due = date.fromisoformat(due_date.strip())
        except ValueError:
            action = await _load_action_or_404(action_service, action_id)
            return render_partial(
                "partials/_action_edit_row.html",
                action=action,
                error="due_date must be YYYY-MM-DD",
            )

    try:
        priority_enum = Priority(priority)
    except ValueError:
        action = await _load_action_or_404(action_service, action_id)
        return render_partial(
            "partials/_action_edit_row.html",
            action=action,
            error=f"Unknown priority: {priority}",
        )

    try:
        updated = await service.edit(
            action_id,
            title=title,
            assignee=assignee or None,
            due_date=parsed_due,
            priority=priority_enum,
        )
    except ValidationError as exc:
        action = await _load_action_or_404(action_service, action_id)
        return render_partial(
            "partials/_action_edit_row.html",
            action=action,
            error=str(exc),
        )
    except Exception:
        logger.exception("web_action_save_failed", action_id=action_id)
        action = await _load_action_or_404(action_service, action_id)
        return render_partial(
            "partials/_action_edit_row.html",
            action=action,
            error="Не удалось сохранить изменения.",
        )
    return render_partial("partials/_action_row.html", action=updated, error=None)


@router.post("/web/actions/{action_id}/confirm", response_class=HTMLResponse)
async def web_action_confirm(
    action_id: int,
    service: ReviewServiceDep,
) -> HTMLResponse:
    updated = await service.confirm(action_id)
    return render_partial("partials/_action_row.html", action=updated, error=None)


@router.post("/web/actions/{action_id}/reject", response_class=HTMLResponse)
async def web_action_reject(
    action_id: int,
    service: ReviewServiceDep,
) -> HTMLResponse:
    updated = await service.reject(action_id)
    return render_partial("partials/_action_row.html", action=updated, error=None)


@router.delete("/web/actions/{action_id}", response_class=HTMLResponse)
async def web_action_delete(
    action_id: int,
    service: ReviewServiceDep,
) -> HTMLResponse:
    await service.delete(action_id)
    return HTMLResponse(content="")