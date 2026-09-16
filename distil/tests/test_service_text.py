"""Tests for :class:`TextService`."""

from __future__ import annotations

import pytest

from app.config import Settings
from app.domain.enums import AuditAction, AuditStatus, TextSource, TextStatus
from app.repositories.fake import FakeAuditRepository, FakeTextRepository
from app.services.audit_service import AuditService
from app.services.exceptions import ValidationError
from app.services.text_service import TextService
from app.services.validation_service import ValidationService


@pytest.fixture
def text_repo() -> FakeTextRepository:
    return FakeTextRepository()


@pytest.fixture
def audit_repo() -> FakeAuditRepository:
    return FakeAuditRepository()


@pytest.fixture
def service(
    text_repo: FakeTextRepository,
    audit_repo: FakeAuditRepository,
) -> TextService:
    settings = Settings(_env_file=None, text_min_length=10, text_max_length=500)
    return TextService(
        repository=text_repo,
        validation=ValidationService(settings),
        audit=AuditService(audit_repo),
    )


async def test_create_persists_and_audits(
    service: TextService,
    audit_repo: FakeAuditRepository,
) -> None:
    entity = await service.create(
        source=TextSource.EMAIL,
        raw_text="A sufficiently long raw text.",
    )
    assert entity.id == 1
    assert entity.status is TextStatus.NEW

    runs = await audit_repo.list()
    assert len(runs) == 1
    assert runs[0].action is AuditAction.CREATE_TEXT
    assert runs[0].status is AuditStatus.OK


async def test_create_invalid_input_does_not_persist(
    service: TextService,
    text_repo: FakeTextRepository,
    audit_repo: FakeAuditRepository,
) -> None:
    with pytest.raises(ValidationError):
        await service.create(source=TextSource.NOTE, raw_text="short")

    assert await text_repo.count() == 0
    runs = await audit_repo.list()
    assert len(runs) == 1
    assert runs[0].status is AuditStatus.ERROR


async def test_get_returns_entity(service: TextService) -> None:
    created = await service.create(
        source=TextSource.MEETING,
        raw_text="A sufficiently long raw text.",
    )
    fetched = await service.get(created.id)
    assert fetched is not None
    assert fetched.id == created.id


async def test_get_missing_returns_none(service: TextService) -> None:
    assert await service.get(12345) is None


async def test_delete_audits_operation(
    service: TextService,
    audit_repo: FakeAuditRepository,
) -> None:
    created = await service.create(
        source=TextSource.NOTE,
        raw_text="A sufficiently long raw text.",
    )
    deleted = await service.delete(created.id)
    assert deleted is True

    actions = [r.action for r in await audit_repo.list()]
    assert AuditAction.DELETE_TEXT in actions


async def test_list_with_stats_passes_filters(
    service: TextService,
) -> None:
    await service.create(
        source=TextSource.EMAIL,
        raw_text="A sufficiently long raw text.",
    )
    await service.create(
        source=TextSource.NOTE,
        raw_text="Another sufficiently long raw text.",
    )

    only_email = await service.list_with_stats(source=TextSource.EMAIL)
    assert len(only_email) == 1
    assert only_email[0].text.source is TextSource.EMAIL