"""Tests for :mod:`app.config`.

Covers the LLM allowlist policy, cross-field validation and env parsing.
"""

from __future__ import annotations

import pytest

from app.config import DEFAULT_ALLOWED_MODELS, Settings


def test_default_model_is_in_allowlist() -> None:
    settings = Settings(_env_file=None)
    assert settings.llm_model == "gpt-4o-mini"
    assert settings.llm_model in settings.llm_allowed_models
    assert tuple(settings.llm_allowed_models) == DEFAULT_ALLOWED_MODELS


def test_model_outside_allowlist_raises() -> None:
    with pytest.raises(ValueError, match="is not allowed"):
        Settings(_env_file=None, llm_model="gpt-4o")


def test_unknown_model_raises() -> None:
    with pytest.raises(ValueError, match="is not allowed"):
        Settings(_env_file=None, llm_model="gpt-5-turbo-preview")


def test_comma_separated_allowlist_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_ALLOWED_MODELS", "gpt-4o-mini,custom-mini")
    monkeypatch.setenv("LLM_MODEL", "custom-mini")
    settings = Settings(_env_file=None)
    assert settings.llm_allowed_models == ["gpt-4o-mini", "custom-mini"]
    assert settings.llm_model == "custom-mini"


def test_invalid_temperature_raises() -> None:
    with pytest.raises(ValueError, match="llm_temperature"):
        Settings(_env_file=None, llm_temperature=3.0)


def test_text_lengths_must_be_ordered() -> None:
    with pytest.raises(ValueError, match="text_min_length"):
        Settings(_env_file=None, text_min_length=100, text_max_length=50)


def test_negative_rate_limit_raises() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        Settings(_env_file=None, rate_limit_per_minute=-1)