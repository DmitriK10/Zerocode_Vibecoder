"""Клиент LLM через proxyapi.ru.

Выбор модели:
    Проект целево использует `gpt-4o-mini` — он дешевле и точнее
    gpt-3.5-turbo при сопоставимой скорости. Допустимые модели
    заданы явным whitelist'ом ниже.

Почему в whitelist нет gpt-3.5-семейства:
    Мы осознанно отказались от 3.5 — она даёт заметно больше ложных
    эскалаций на нашем промпте. Держать модели, которые не используются,
    означает неявный техдолг: разработчик вынужден проверять, зачем они
    там. Если понадобится временно вернуть 3.5 — добавь её в
    SUPPORTED_MODELS и снабди комментарием-обоснованием.

Зачем whitelist:
    Защита от опечаток в .env (например, 'gpt-4o-minni'). Опечатка
    должна валить приложение при старте, а не превращаться в 500 от API
    в момент первого запроса.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Set

from openai import OpenAI

from src.services.prompts import SYSTEM_PROMPT, build_user_prompt


# Whitelist поддерживаемых моделей через ChatCompletion API.
# Состав подобран под реальные задачи проекта; расширять только осознанно.
SUPPORTED_MODELS: Set[str] = {
    # --- GPT-4o family (рекомендуемые) ---
    "gpt-4o",
    "gpt-4o-mini",
    # --- GPT-4 family ---
    "gpt-4",
    "gpt-4-turbo",
    "gpt-4-turbo-preview",
}


class LLMParsingError(RuntimeError):
    """Не удалось извлечь валидный JSON из ответа модели."""


def enforce_supported_model_policy(model: str) -> None:
    """Проверить, что модель входит в поддерживаемый whitelist.

    Raises:
        ValueError: если модели нет в SUPPORTED_MODELS.
            Это не ограничение возможностей, а защита от опечаток.
    """
    if model not in SUPPORTED_MODELS:
        raise ValueError(
            f"Model '{model}' is not in the supported whitelist. "
            f"Supported: {sorted(SUPPORTED_MODELS)}. "
            f"To add a new model, extend SUPPORTED_MODELS in "
            f"src/infrastructure/llm_client.py."
        )


# Регулярка для ```json ... ``` (с опциональным языком).
_FENCE_RE = re.compile(
    r"```(?:json|JSON)?\s*(?P<body>.*?)\s*```",
    re.DOTALL,
)


def extract_json_object(raw_content: str) -> Dict[str, Any]:
    """Извлечь JSON-объект из «сырого» ответа модели.

    Обрабатывает кейсы:
        1. Чистый JSON:                '{"a": 1}'
        2. Markdown-забор:             '```json\\n{"a": 1}\\n```'
        3. Текст + JSON + текст:       'Вот результат: {"a": 1}. Готово.'
        4. Забор + пояснение вокруг:   'Sure!\\n```json\\n{"a": 1}\\n```\\nDone.'

    Raises:
        LLMParsingError: если валидный JSON-объект не найден.
    """
    if not raw_content or not raw_content.strip():
        raise LLMParsingError("Empty response from LLM")

    text = raw_content.strip()

    # 1) Markdown-забор
    fence = _FENCE_RE.search(text)
    if fence:
        candidate = fence.group("body").strip()
        parsed = _try_load(candidate)
        if parsed is not None:
            return parsed

    # 2) Просто валидный JSON целиком
    parsed = _try_load(text)
    if parsed is not None:
        return parsed

    # 3) Первый {...} блок в произвольном тексте
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        parsed = _try_load(candidate)
        if parsed is not None:
            return parsed

    raise LLMParsingError(
        f"Could not extract JSON object from LLM response. "
        f"First 200 chars: {raw_content[:200]!r}"
    )


def _try_load(candidate: str) -> Dict[str, Any] | None:
    """Попробовать распарсить строку как JSON-объект. None — если не вышло."""
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if isinstance(value, dict):
        return value
    return None


class ProxyOpenAIClient:
    """Реализация порта LLMClient через proxyapi.ru."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float = 0.2,
        timeout: float = 30.0,
    ) -> None:
        enforce_supported_model_policy(model)
        self._client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self._model = model
        self._temperature = temperature

    def extract(self, text: str) -> Dict[str, Any]:
        """Вызвать LLM и вернуть распарсенный JSON как dict.

        Raises:
            LLMParsingError: если ответ модели не содержит валидного JSON.
            openai.*: пробрасываются наверх для эскалации в сервисе.
        """
        response = self._client.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(text)},
            ],
        )
        content = response.choices[0].message.content or ""
        return extract_json_object(content)