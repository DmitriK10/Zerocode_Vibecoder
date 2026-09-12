"""Тесты конфигурации smoke-теста: URL и таймаут из окружения.

Сам HTTP-вызов не тестируется — он живёт в _post_ingest и подменяется
через httpx в ручном прогоне. Здесь проверяем только разбор переменных
окружения и краевые случаи.
"""
from __future__ import annotations

import pytest

import smoke_test


# --- _resolve_base_url ----------------------------------------------------

def test_base_url_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SMOKE_BASE_URL", raising=False)
    assert smoke_test._resolve_base_url() == smoke_test.DEFAULT_BASE_URL


def test_base_url_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMOKE_BASE_URL", "http://127.0.0.1:8001")
    assert smoke_test._resolve_base_url() == "http://127.0.0.1:8001"


def test_base_url_empty_string_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMOKE_BASE_URL", "   ")
    assert smoke_test._resolve_base_url() == smoke_test.DEFAULT_BASE_URL


# --- _resolve_timeout -----------------------------------------------------

def test_timeout_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SMOKE_TIMEOUT", raising=False)
    assert smoke_test._resolve_timeout() == smoke_test.DEFAULT_TIMEOUT_SECONDS


def test_timeout_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMOKE_TIMEOUT", "90")
    assert smoke_test._resolve_timeout() == 90.0


def test_timeout_invalid_string_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMOKE_TIMEOUT", "abc")
    assert smoke_test._resolve_timeout() == smoke_test.DEFAULT_TIMEOUT_SECONDS


def test_timeout_negative_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMOKE_TIMEOUT", "-5")
    assert smoke_test._resolve_timeout() == smoke_test.DEFAULT_TIMEOUT_SECONDS


# --- _resolve_text --------------------------------------------------------

def test_text_default() -> None:
    assert smoke_test._resolve_text(["smoke_test.py"]) == smoke_test.DEFAULT_TEXT


def test_text_from_argv() -> None:
    assert smoke_test._resolve_text(["smoke_test.py", "Привет"]) == "Привет"