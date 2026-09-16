"""Application configuration.

This module is the single source of truth for runtime settings.

Policy notes
------------
* The project permits ONLY models present in ``llm_allowed_models``.
  By default the allowlist contains a single model: ``gpt-4o-mini``.
* The allowlist is the SINGLE source of truth for model policy. The LLM
  client validates the configured model against the allowlist it receives
  from :class:`Settings` — there is no separate hard-coded policy.
* The legacy ``openai.ChatCompletion`` interface is no longer part of the
  modern OpenAI SDK and MUST NOT be used. Any attempt to run with a model
  outside the allowlist raises :class:`ValueError` at startup.
* All external LLM calls go through ``proxyapi.ru`` (see ``LLM_BASE_URL``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
ENV_FILE: Path = PROJECT_ROOT / ".env"

DEFAULT_ALLOWED_MODELS: tuple[str, ...] = ("gpt-4o-mini",)

DEFAULT_CORS_ORIGINS: tuple[str, ...] = (
    "http://localhost:8000",
    "http://127.0.0.1:8000",
)


class Settings(BaseSettings):
    """Runtime configuration loaded from environment and ``.env``."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application -------------------------------------------------------
    app_name: str = "distil"
    app_env: Literal["local", "test", "production"] = "local"
    app_debug: bool = False
    app_host: str = "0.0.0.0"  # noqa: S104 — bound inside a container
    app_port: int = 8000

    # --- CORS --------------------------------------------------------------
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: list(DEFAULT_CORS_ORIGINS)
    )

    # --- Database ----------------------------------------------------------
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/distil"
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout_seconds: int = 30

    # --- LLM ---------------------------------------------------------------
    llm_base_url: str = "https://api.proxyapi.ru/openai/v1"
    llm_api_key: SecretStr = SecretStr("sk-placeholder")
    llm_model: str = "gpt-4o-mini"
    llm_allowed_models: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: list(DEFAULT_ALLOWED_MODELS)
    )
    llm_temperature: float = 0.1
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 0

    # --- Text limits -------------------------------------------------------
    text_min_length: int = 10
    text_max_length: int = 20_000

    # --- Audit -------------------------------------------------------------
    audit_retention_days: int = 30

    # --- Rate limiting -----------------------------------------------------
    rate_limit_per_minute: int = 60

    # --- HTTP auth (optional) ---------------------------------------------
    api_auth_enabled: bool = False
    api_auth_username: str | None = None
    api_auth_password: SecretStr | None = None

    # -- Validators ---------------------------------------------------------
    @field_validator("llm_allowed_models", "cors_origins", mode="before")
    @classmethod
    def _split_comma_separated(cls, value: object) -> object:
        """Allow comma-separated values in env (e.g. ``a,b,c``).

        Also accepts a JSON array (``["a","b"]``) because
        :class:`pydantic-settings` parses JSON by default.
        """
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                # Let pydantic parse it as JSON.
                return value
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return value

    @field_validator("llm_temperature")
    @classmethod
    def _validate_temperature(cls, value: float) -> float:
        if not 0.0 <= value <= 2.0:
            raise ValueError(f"llm_temperature must be in [0.0, 2.0], got {value!r}")
        return value

    @field_validator("text_min_length", "text_max_length")
    @classmethod
    def _validate_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("text length limits must be positive")
        return value

    @field_validator(
        "db_pool_size",
        "db_max_overflow",
        "llm_timeout_seconds",
        "audit_retention_days",
        "rate_limit_per_minute",
    )
    @classmethod
    def _validate_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("value must be non-negative")
        return value

    # -- Post-init policy checks -------------------------------------------
    def model_post_init(self, __context: object) -> None:
        if self.text_min_length >= self.text_max_length:
            raise ValueError(
                "text_min_length must be strictly less than text_max_length "
                f"({self.text_min_length} >= {self.text_max_length})"
            )
        self.assert_model_allowed()
        self.assert_auth_config()

    def assert_model_allowed(self) -> None:
        """Fail fast if the configured LLM model is not in the allowlist."""
        if not self.llm_allowed_models:
            raise ValueError("llm_allowed_models must not be empty")
        if self.llm_model not in self.llm_allowed_models:
            raise ValueError(
                f"Model {self.llm_model!r} is not allowed. "
                f"Allowed models: {self.llm_allowed_models}. "
                "Update LLM_ALLOWED_MODELS to add a new model."
            )

    def assert_auth_config(self) -> None:
        """Fail fast if auth is enabled but credentials are missing."""
        if not self.api_auth_enabled:
            return
        if not self.api_auth_username or not self.api_auth_password:
            raise ValueError(
                "API_AUTH_ENABLED=true requires API_AUTH_USERNAME and "
                "API_AUTH_PASSWORD to be set."
            )
        if len(self.api_auth_password.get_secret_value()) < 8:
            raise ValueError(
                "API_AUTH_PASSWORD must be at least 8 characters long."
            )

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql+asyncpg")

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite+aiosqlite")


def get_settings() -> Settings:
    """Return a fresh :class:`Settings` instance.

    Deliberately NOT cached: caching the process-wide settings instance is
    a well-known source of cross-test pollution (a test mutates env vars
    and another test sees stale values). Applications that want caching
    should store the instance on ``app.state.settings`` — see
    :func:`app.main.create_app`.
    """
    return Settings()