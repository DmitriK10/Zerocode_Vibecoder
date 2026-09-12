"""Конфигурация приложения.

Единственная точка доступа к настройкам. Источники (по приоритету):
    1. Переменные окружения процесса.
    2. Файл .env в корне проекта (рядом с src/).
    3. Значения по умолчанию (только для НЕ-секретных политик).

BASE_DIR вычисляется от расположения этого файла, а не хардкодится:
    src/config.py → parents[1] = корень проекта.
Это делает проект переносимым между машинами без правки кода.

Секреты (PROXY_API_KEY) без значения в env/.env не имеют дефолта
и приводят к ошибке валидации при старте — fail fast.

Дефолт LLM_MODEL согласован с README и whitelist'ом в llm_client.py.
Это gpt-4o-mini — основная модель проекта.
"""
from __future__ import annotations

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


# --- Пути (абсолютные, вычисляются от __file__) ---------------------------
# __file__ = <project>\src\config.py
# parents[0] = <project>\src
# parents[1] = <project>
BASE_DIR: Path = Path(__file__).resolve().parents[1]
ENV_FILE: Path = BASE_DIR / ".env"
DATA_DIR: Path = BASE_DIR / "data"


class Settings(BaseSettings):
    """Типизированные настройки приложения."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # --- Proxy API --------------------------------------------------------
    # Секрет: обязателен, без дефолта. Fail fast, если не задан.
    PROXY_API_KEY: SecretStr
    PROXY_API_BASE_URL: str = Field(
        default="https://api.proxyapi.ru/openai/v1"
    )

    # --- LLM --------------------------------------------------------------
    # Основная модель проекта — gpt-4o-mini (дешевле и точнее 3.5).
    # Whitelist проверяется в llm_client.enforce_supported_model_policy().
    LLM_MODEL: str = Field(default="gpt-4o-mini")
    LLM_TEMPERATURE: float = Field(default=0.2, ge=0.0, le=2.0)
    LLM_TIMEOUT_SECONDS: float = Field(default=30.0, gt=0.0)

    # --- Storage ----------------------------------------------------------
    DB_PATH: Path = Field(default=DATA_DIR / "processing.db")

    def ensure_directories(self) -> None:
        """Создать каталоги, необходимые для работы (idempotent)."""
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)


_settings_singleton: Settings | None = None


def get_settings() -> Settings:
    """Вернуть singleton настроек (ленивая инициализация)."""
    global _settings_singleton
    if _settings_singleton is None:
        _settings_singleton = Settings()
    return _settings_singleton