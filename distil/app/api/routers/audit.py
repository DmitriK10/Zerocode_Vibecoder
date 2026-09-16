"""Audit router: read-only access to ``audit_runs``."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import AuditServiceDep
from app.domain.enums import AuditAction, AuditStatus
from app.schemas.api import AuditRunRead
from app.services.exceptions import NotFoundError

router = APIRouter()


@router.get(
    "/audit",
    response_model=list[AuditRunRead],
    summary="List audit records (newest first)",
)
async def list_audit(
    service: AuditServiceDep,
    audit_status: Annotated[AuditStatus | None, Query(alias="status")] = None,
    action: Annotated[AuditAction | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AuditRunRead]:
    runs = await service.list_runs(
        status=audit_status,
        action=action,
        limit=limit,
        offset=offset,
    )
    return [AuditRunRead.model_validate(r) for r in runs]


@router.get(
    "/audit/{audit_id}",
    response_model=AuditRunRead,
    summary="Get a single audit record",
)
async def get_audit(
    audit_id: int,
    service: AuditServiceDep,
) -> AuditRunRead:
    entity = await service.get_by_id(audit_id)
    if entity is None:
        raise NotFoundError(f"Audit run {audit_id} not found")
    return AuditRunRead.model_validate(entity)