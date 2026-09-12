"""FastAPI-приложение: точка входа POST /ingest + журнал /log.

Composition root вынесен в src/bootstrap.py. Здесь только singleton-обёртки,
чтобы на процесс был один экземпляр репозитория и сервиса.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from src.bootstrap import build_llm_client, build_repository
from src.config import Settings, get_settings
from src.infrastructure.repository import SQLiteProcessingRepository
from src.services.processor import ProcessingService


# --- Schemas API ----------------------------------------------------------
class IngestRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)


class IngestResponse(BaseModel):
    id: int
    status: str
    escalate: bool
    result: Dict[str, Any]


# --- Singletons (composition root) ----------------------------------------
@lru_cache(maxsize=1)
def _repo_singleton() -> SQLiteProcessingRepository:
    """Единственный на процесс экземпляр репозитория."""
    return build_repository(get_settings())


def get_repository() -> SQLiteProcessingRepository:
    """FastAPI-зависимость для чтения журнала."""
    return _repo_singleton()


def _build_service_singleton(settings: Settings) -> ProcessingService:
    """Собрать сервис с общим репозиторием."""
    settings.ensure_directories()
    return ProcessingService(
        llm_client=build_llm_client(settings),
        repository=_repo_singleton(),
        model_name=settings.LLM_MODEL,
    )


@lru_cache(maxsize=1)
def _service_singleton() -> ProcessingService:
    return _build_service_singleton(get_settings())


def get_service() -> ProcessingService:
    """FastAPI-зависимость: единый сервис на процесс."""
    return _service_singleton()


# --- App ------------------------------------------------------------------
app = FastAPI(title="LLM Process MVP", version="1.0.0")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse)
def ingest(
    payload: IngestRequest,
    service: ProcessingService = Depends(get_service),
) -> IngestResponse:
    record = service.process(payload.text)
    return IngestResponse(
        id=record.id or 0,
        status=record.status.value,
        escalate=bool(record.result.escalate) if record.result else True,
        result=record.result.model_dump(mode="json") if record.result else {},
    )


@app.get("/log")
def read_log(
    limit: int = 20,
    repo: SQLiteProcessingRepository = Depends(get_repository),
) -> List[Dict[str, Any]]:
    """Журнал аудита: последние записи из SQLite.

    LLM здесь не нужен — используем только репозиторий, чтобы чтение
    журнала не зависело от состояния proxyapi-ключа.
    """
    return [r.model_dump(mode="json") for r in repo.list_recent(limit)]