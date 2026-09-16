"""Texts router: create, list, detail, delete."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import ActionServiceDep, TextServiceDep
from app.domain.enums import TextSource, TextStatus
from app.schemas.api import ActionRead, TextCreate, TextDetail, TextRead, TextSummary
from app.services.exceptions import NotFoundError

router = APIRouter()


@router.post(
    "/texts",
    response_model=TextRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new text for later extraction",
)
async def create_text(
    payload: TextCreate,
    service: TextServiceDep,
) -> TextRead:
    entity = await service.create(source=payload.source, raw_text=payload.raw_text)
    return TextRead.model_validate(entity)


@router.get(
    "/texts",
    response_model=list[TextSummary],
    summary="Showcase list of texts with action counts",
)
async def list_texts(
    service: TextServiceDep,
    has_review_required: Annotated[bool | None, Query()] = None,
    source: Annotated[TextSource | None, Query()] = None,
    text_status: Annotated[TextStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TextSummary]:
    rows = await service.list_with_stats(
        has_review_required=has_review_required,
        source=source,
        status=text_status,
        limit=limit,
        offset=offset,
    )
    return [
        TextSummary.from_stats(
            row.text, row.actions_count, row.needs_review_count
        )
        for row in rows
    ]


@router.get(
    "/texts/{text_id}",
    response_model=TextDetail,
    summary="Get a text with its extracted actions",
)
async def get_text(
    text_id: int,
    text_service: TextServiceDep,
    action_service: ActionServiceDep,
) -> TextDetail:
    text = await text_service.get(text_id)
    if text is None:
        raise NotFoundError(f"Text {text_id} not found")
    actions = await action_service.list_by_text(text_id)
    return TextDetail(
        text=TextRead.model_validate(text),
        actions=[ActionRead.model_validate(a) for a in actions],
    )


@router.delete(
    "/texts/{text_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a text (cascades to its actions)",
)
async def delete_text(
    text_id: int,
    service: TextServiceDep,
) -> None:
    deleted = await service.delete(text_id)
    if not deleted:
        raise NotFoundError(f"Text {text_id} not found")