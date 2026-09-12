"""Тесты конфигурации: приоритет источников, fail fast, валидация."""
from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from src import config as cfg
from src.config import Settings


def test_base_dir_points_to_project_root() -> None:
    """BASE_DIR вычисляется от __file__, а не хардкодится."""
    assert cfg.BASE_DIR.is_absolute()
    assert (cfg.BASE_DIR / "src").is_dir()
    assert cfg.ENV_FILE == cfg.BASE_DIR / ".env"
    assert cfg.DATA_DIR == cfg.BASE_DIR / "data"


def test_default_model_is_gpt_4o_mini(monkeypatch: pytest.MonkeyPatch) -> None:
    """Регресс: дефолтная модель должна совпадать с README и whitelist.

    Ранее default='gpt-3.5-turbo-16k' противоречил документации и
    приводил к тихому откату на старую модель, если .env не прочитался.
    """
    monkeypatch.setenv("PROXY_API_KEY", "sk-test")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.LLM_MODEL == "gpt-4o-mini"


def test_settings_reads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROXY_API_KEY", "sk-test-123")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.2")
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.PROXY_API_KEY.get_secret_value() == "sk-test-123"
    assert s.LLM_MODEL == "gpt-4o-mini"
    assert s.LLM_TEMPERATURE == 0.2


def test_settings_fails_without_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PROXY_API_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_temperature_bounds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROXY_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_TEMPERATURE", "5.0")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_db_path_default_is_absolute_and_under_project(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROXY_API_KEY", "sk-test")
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert isinstance(s.DB_PATH, Path)
    assert s.DB_PATH.is_absolute()
    assert str(s.DB_PATH).startswith(str(cfg.BASE_DIR))