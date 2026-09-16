"""Tests for :class:`AuditService`."""

from __future__ import annotations

import pytest

from app.domain.enums import AuditAction, AuditStatus
from app.repositories.fake import FakeAuditRepository
from app.services.audit_service import AuditService


@pytest.fixture
def repo() -> FakeAuditRepository:
    return FakeAuditRepository()


@pytest.fixture
def service(repo: FakeAuditRepository) -> AuditService:
    return AuditService(repo)


async def test_record_success_writes_ok(service: AuditService) -> None:
    entity = await service.record_success(
        action=AuditAction.CREATE_TEXT,
        duration_ms=12,
        input_payload={"source": "email"},
        output_payload={"text_id": 1},
    )
    assert entity.status is AuditStatus.OK
    assert entity.action is AuditAction.CREATE_TEXT
    assert entity.duration_ms == 12
    assert entity.input_payload == {"source": "email"}
    assert entity.output_payload == {"text_id": 1}
    assert entity.needs_review_count == 0
    assert entity.error is None


async def test_record_error_writes_error(service: AuditService) -> None:
    entity = await service.record_error(
        action=AuditAction.EXTRACT_ACTIONS,
        duration_ms=500,
        error="upstream timeout",
        input_payload={"text_id": 7},
    )
    assert entity.status is AuditStatus.ERROR
    assert entity.error == "upstream timeout"
    assert entity.output_payload is None


async def test_list_filters_by_status(service: AuditService) -> None:
    await service.record_success(
        action=AuditAction.CREATE_TEXT, duration_ms=1
    )
    await service.record_error(
        action=AuditAction.EXTRACT_ACTIONS, duration_ms=2, error="x"
    )
    errors = await service.list_runs(status=AuditStatus.ERROR)
    assert len(errors) == 1
    assert errors[0].error == "x"


async def test_list_filters_by_action(service: AuditService) -> None:
    await service.record_success(
        action=AuditAction.CREATE_TEXT, duration_ms=1
    )
    await service.record_success(
        action=AuditAction.MANUAL_REVIEW, duration_ms=1
    )
    runs = await service.list_runs(action=AuditAction.MANUAL_REVIEW)
    assert len(runs) == 1
    assert runs[0].action is AuditAction.MANUAL_REVIEW


async def test_get_by_id_returns_entity(service: AuditService) -> None:
    created = await service.record_success(
        action=AuditAction.CREATE_TEXT, duration_ms=1
    )
    fetched = await service.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id