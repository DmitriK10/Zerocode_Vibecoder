"""Composition root проекта: единая сборка адаптеров из настроек.

Сюда вынесены все места, где домен/сервис связывается с конкретными
реализациями (OpenAI-прокси, SQLite). И `src/api/app.py`, и `run_batch.py`,
и любые будущие entrypoint'ы используют эти функции, чтобы не дублировать
сборку и не расходиться при изменении сигнатур адаптеров.
"""
from __future__ import annotations

from src.config import Settings
from src.infrastructure.llm_client import ProxyOpenAIClient
from src.infrastructure.repository import SQLiteProcessingRepository
from src.services.processor import ProcessingService


def build_repository(settings: Settings) -> SQLiteProcessingRepository:
    """Собрать репозиторий журнала аудита.

    SQLiteProcessingRepository сам создаёт каталог под БД в __init__,
    поэтому отдельный ensure_directories() здесь не нужен.
    """
    return SQLiteProcessingRepository(settings.DB_PATH)


def build_llm_client(settings: Settings) -> ProxyOpenAIClient:
    """Собрать LLM-клиент с валидацией модели по whitelist."""
    return ProxyOpenAIClient(
        api_key=settings.PROXY_API_KEY.get_secret_value(),
        base_url=settings.PROXY_API_BASE_URL,
        model=settings.LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        timeout=settings.LLM_TIMEOUT_SECONDS,
    )


def build_service(settings: Settings) -> ProcessingService:
    """Собрать ProcessingService из адаптеров.

    Создаёт новый экземпляр репозитория — для FastAPI-пути используется
    singleton-обёртка в src/api/app.py, чтобы репозиторий был один на процесс.
    """
    settings.ensure_directories()
    return ProcessingService(
        llm_client=build_llm_client(settings),
        repository=build_repository(settings),
        model_name=settings.LLM_MODEL,
    )