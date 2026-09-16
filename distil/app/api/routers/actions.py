"""Actions router: read and manually review extracted actions."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import ActionServiceDep, ReviewServiceDep
from app.schemas.api import ActionEditRequest, ActionRead
from app.services.exceptions import NotFoundError

router = APIRouter()


@router.get(
    "/actions/{action_id}",
    response_model=ActionRead,
    summary="Get a single action",
)
async def get_action(
    action_id: int,
    service: ActionServiceDep,
) -> ActionRead:
    entity = await service.get(action_id)
    if entity is None:
        raise NotFoundError(f"Action {action_id} not found")
    return ActionRead.model_validate(entity)


@router.patch(
    "/actions/{action_id}",
    response_model=ActionRead,
    summary="Edit an action and mark it as manually edited",
)
async def edit_action(
    action_id: int,
    payload: ActionEditRequest,
    service: ReviewServiceDep,
) -> ActionRead:
    updated = await service.edit(
        action_id,
        title=payload.title,
        assignee=payload.assignee,
        due_date=payload.due_date,
        priority=payload.priority,
    )
    return ActionRead.model_validate(updated)


@router.post(
    "/actions/{action_id}/confirm",
    response_model=ActionRead,
    summary="Confirm an action (clears needs_review)",
)
async def confirm_action(
    action_id: int,
    service: ReviewServiceDep,
) -> ActionRead:
    updated = await service.confirm(action_id)
    return ActionRead.model_validate(updated)


@router.post(
    "/actions/{action_id}/reject",
    response_model=ActionRead,
    summary="Reject an action",
)
async def reject_action(
    action_id: int,
    service: ReviewServiceDep,
) -> ActionRead:
    updated = await service.reject(action_id)
    return ActionRead.model_validate(updated)


@router.delete(
    "/actions/{action_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an action",
)
async def delete_action(
    action_id: int,
    service: ReviewServiceDep,
) -> None:
    deleted = await service.delete(action_id)
    if not deleted:
        raise NotFoundError(f"Action {action_id} not found")