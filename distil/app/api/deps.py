"""FastAPI dependency providers.

All wiring lives here. Endpoints depend on the service classes, services
depend on repository/LLM protocols. Tests override the repository and LLM
providers to plug in fakes.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.session import get_session
from app.llm.protocol import LLMClientProtocol
from app.llm.proxyapi_client import ProxyApiLLMClient
from app.repositories.postgres import (
    PostgresActionRepository,
    PostgresAuditRepository,
    PostgresTextRepository,
)
from app.repositories.protocols import (
    ActionRepositoryProtocol,
    AuditRepositoryProtocol,
    TextRepositoryProtocol,
)
from app.services.action_service import ActionService
from app.services.audit_service import AuditService
from app.services.extraction_service import ExtractionService
from app.services.review_service import ReviewService
from app.services.text_service import TextService
from app.services.validation_service import ValidationService

# --------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------


def get_settings_dep(request: Request) -> Settings:
    """Return the settings attached to the running application."""
    return cast(Settings, request.app.state.settings)


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]

# --------------------------------------------------------------------------
# Sessions
# --------------------------------------------------------------------------

SessionDep = Annotated[AsyncSession, Depends(get_session)]


# --------------------------------------------------------------------------
# Repositories (PostgreSQL by default; overridden in tests)
# --------------------------------------------------------------------------


def get_text_repository(session: SessionDep) -> TextRepositoryProtocol:
    return PostgresTextRepository(session)


def get_action_repository(session: SessionDep) -> ActionRepositoryProtocol:
    return PostgresActionRepository(session)


def get_audit_repository(session: SessionDep) -> AuditRepositoryProtocol:
    return PostgresAuditRepository(session)


TextRepoDep = Annotated[TextRepositoryProtocol, Depends(get_text_repository)]
ActionRepoDep = Annotated[ActionRepositoryProtocol, Depends(get_action_repository)]
AuditRepoDep = Annotated[AuditRepositoryProtocol, Depends(get_audit_repository)]


# --------------------------------------------------------------------------
# LLM client (lazy; constructed on first use)
# --------------------------------------------------------------------------


@lru_cache(maxsize=4)
def _build_llm_client(
    api_key: str,
    base_url: str,
    model: str,
    allowed_models: tuple[str, ...],
    temperature: float,
    timeout_seconds: int,
) -> ProxyApiLLMClient:
    return ProxyApiLLMClient(
        api_key=api_key,
        base_url=base_url,
        model=model,
        allowed_models=list(allowed_models),
        temperature=temperature,
        timeout_seconds=timeout_seconds,
    )


def get_llm_client(settings: SettingsDep) -> LLMClientProtocol:
    return _build_llm_client(
        api_key=settings.llm_api_key.get_secret_value(),
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        allowed_models=tuple(settings.llm_allowed_models),
        temperature=settings.llm_temperature,
        timeout_seconds=settings.llm_timeout_seconds,
    )


LLMClientDep = Annotated[LLMClientProtocol, Depends(get_llm_client)]


# --------------------------------------------------------------------------
# Services
# --------------------------------------------------------------------------


def get_audit_service(audit_repo: AuditRepoDep) -> AuditService:
    return AuditService(audit_repo)


def get_validation_service(settings: SettingsDep) -> ValidationService:
    return ValidationService(settings)


def get_text_service(
    text_repo: TextRepoDep,
    validation: Annotated[ValidationService, Depends(get_validation_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> TextService:
    return TextService(repository=text_repo, validation=validation, audit=audit)


def get_action_service(action_repo: ActionRepoDep) -> ActionService:
    return ActionService(action_repo)


def get_extraction_service(
    text_repo: TextRepoDep,
    action_repo: ActionRepoDep,
    llm: LLMClientDep,
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> ExtractionService:
    return ExtractionService(
        text_repository=text_repo,
        action_repository=action_repo,
        llm_client=llm,
        audit=audit,
    )


def get_review_service(
    action_repo: ActionRepoDep,
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> ReviewService:
    return ReviewService(repository=action_repo, audit=audit)


AuditServiceDep = Annotated[AuditService, Depends(get_audit_service)]
TextServiceDep = Annotated[TextService, Depends(get_text_service)]
ActionServiceDep = Annotated[ActionService, Depends(get_action_service)]
ExtractionServiceDep = Annotated[ExtractionService, Depends(get_extraction_service)]
ReviewServiceDep = Annotated[ReviewService, Depends(get_review_service)]


# --------------------------------------------------------------------------
# Session as async iterator (for health check)
# --------------------------------------------------------------------------


async def session_dependency() -> AsyncIterator[AsyncSession]:
    """Alias for :func:`get_session` so tests can override it cleanly."""
    async for s in get_session():
        yield s