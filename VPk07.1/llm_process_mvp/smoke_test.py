"""Smoke-тест: отправить один вход в работающий сервер и красиво напечатать JSON.

Скрипт автономен — не читает .env и не тянет src.config.Settings.
Это сделано намеренно: smoke-тест проверяет работающий сервер, а не
конфигурацию текущего процесса. Настройки берутся из переменных окружения
процесса (или из дефолтов), чтобы не путать конфиги клиента и сервера.

Запуск (при поднятом uvicorn):
    python smoke_test.py "Не пришёл счёт за март, заказ 42"
    python smoke_test.py "Привет"           # проверка эскалации
    python smoke_test.py                    # вход по умолчанию

Переопределение адреса и таймаута (PowerShell):
    $env:SMOKE_BASE_URL = "http://127.0.0.1:8001"
    $env:SMOKE_TIMEOUT  = "90"
    python smoke_test.py "тест"
"""
from __future__ import annotations

import json
import os
import sys

import httpx


DEFAULT_BASE_URL: str = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT_SECONDS: float = 60.0
DEFAULT_TEXT: str = "Не пришёл счёт за март, заказ 42"


def _resolve_base_url() -> str:
    """Вернуть базовый URL сервера из SMOKE_BASE_URL или дефолт."""
    value = os.getenv("SMOKE_BASE_URL", "").strip()
    return value or DEFAULT_BASE_URL


def _resolve_timeout() -> float:
    """Вернуть таймаут из SMOKE_TIMEOUT или дефолт. Невалидное → дефолт."""
    raw = os.getenv("SMOKE_TIMEOUT", "").strip()
    if not raw:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS
    return value if value > 0 else DEFAULT_TIMEOUT_SECONDS


def _resolve_text(argv: list[str]) -> str:
    """Взять текст из argv[1] или вернуть дефолт."""
    if len(argv) > 1:
        return argv[1]
    return DEFAULT_TEXT


def _post_ingest(base_url: str, text: str, timeout: float) -> httpx.Response:
    """Отправить POST /ingest. Вынесено для тестируемости (легко подменить)."""
    return httpx.post(
        f"{base_url}/ingest",
        json={"text": text},
        timeout=timeout,
    )


def main(argv: list[str] | None = None) -> int:
    """Точка входа. argv — для тестируемости, по умолчанию sys.argv."""
    args = sys.argv if argv is None else argv
    base_url = _resolve_base_url()
    timeout = _resolve_timeout()
    text = _resolve_text(args)

    print(f"[input]  {text!r}")
    print(f"[target] {base_url}  (timeout={timeout}s)")

    try:
        resp = _post_ingest(base_url, text, timeout)
    except httpx.ConnectError:
        print(f"[error]  Сервер {base_url} недоступен. Запусти uvicorn в другом окне.")
        return 2
    except httpx.TimeoutException:
        print(f"[error]  Превышен таймаут {timeout}s. Проверь LLM/прокси.")
        return 3

    print(f"[status] HTTP {resp.status_code}")
    if resp.status_code != 200:
        print(resp.text)
        return 1

    data = resp.json()
    print(f"[id]     {data['id']}")
    print(f"[state]  {data['status']}  (escalate={data['escalate']})")
    print("[result]")
    print(json.dumps(data["result"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())