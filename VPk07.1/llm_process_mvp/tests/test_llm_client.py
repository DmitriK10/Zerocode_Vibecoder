"""Тесты политики модели и парсинга JSON из ответа LLM."""
from __future__ import annotations

import pytest

from src.infrastructure.llm_client import (
    LLMParsingError,
    enforce_supported_model_policy,
    extract_json_object,
)


# --- Политика поддерживаемых моделей -------------------------------------

def test_gpt_4o_mini_is_allowed() -> None:
    """Основная модель проекта — gpt-4o-mini."""
    enforce_supported_model_policy("gpt-4o-mini")


def test_gpt_4o_is_allowed() -> None:
    enforce_supported_model_policy("gpt-4o")


def test_gpt_4_family_is_allowed() -> None:
    """GPT-4 семейство остаётся в whitelist как запасной вариант."""
    enforce_supported_model_policy("gpt-4")
    enforce_supported_model_policy("gpt-4-turbo")
    enforce_supported_model_policy("gpt-4-turbo-preview")


def test_gpt_35_is_not_allowed_anymore() -> None:
    """Регресс: gpt-3.5-семейство осознанно исключено из whitelist.

    Мы отказались от 3.5 в пользу 4o-mini (меньше ложных эскалаций).
    Если этот тест падает — значит кто-то вернул 3.5 в SUPPORTED_MODELS.
    В этом случае надо: 1) обновить этот тест с обоснованием и
    2) убедиться, что README и .env.example согласованы.
    """
    for legacy in (
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
        "gpt-3.5-turbo-0125",
        "gpt-3.5-turbo-1106",
        "gpt-3.5-turbo-instruct",
    ):
        with pytest.raises(ValueError):
            enforce_supported_model_policy(legacy)


def test_typo_model_raises_value_error() -> None:
    """Опечатка в .env должна валить при старте, а не в рантайме."""
    with pytest.raises(ValueError) as exc:
        enforce_supported_model_policy("gpt-4o-minni")
    assert "supported whitelist" in str(exc.value)


def test_unknown_model_raises_value_error() -> None:
    with pytest.raises(ValueError):
        enforce_supported_model_policy("totally-unknown-model")


# --- Парсинг JSON ---------------------------------------------------------

def test_clean_json() -> None:
    raw = '{"category": "billing", "summary": "x"}'
    assert extract_json_object(raw) == {"category": "billing", "summary": "x"}


def test_markdown_fence_with_language() -> None:
    raw = '```json\n{"a": 1, "b": 2}\n```'
    assert extract_json_object(raw) == {"a": 1, "b": 2}


def test_markdown_fence_without_language() -> None:
    raw = '```\n{"a": 1}\n```'
    assert extract_json_object(raw) == {"a": 1}


def test_text_around_json() -> None:
    raw = 'Вот результат: {"a": 1, "b": "ok"}. Готово.'
    assert extract_json_object(raw) == {"a": 1, "b": "ok"}


def test_fence_with_surrounding_text() -> None:
    raw = 'Sure!\n```json\n{"a": 1}\n```\nDone.'
    assert extract_json_object(raw) == {"a": 1}


def test_empty_response_raises() -> None:
    with pytest.raises(LLMParsingError):
        extract_json_object("")


def test_no_json_raises() -> None:
    with pytest.raises(LLMParsingError):
        extract_json_object("Извините, я не могу помочь с этим запросом.")


def test_json_array_is_not_accepted() -> None:
    """Схема — объект, массив не подходит."""
    with pytest.raises(LLMParsingError):
        extract_json_object("[1, 2, 3]")