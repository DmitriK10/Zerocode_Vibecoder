"""Тесты системного промпта: контракт по эскалации, языку и формату JSON.

Не тестируем поведение LLM (это делается вручную в batch-прогоне), но
фиксируем критичные инварианты промпта, чтобы случайная правка не сломала
правило 'escalate=false по умолчанию', правило языка или обязательную
эскалацию для спама.
"""
from __future__ import annotations

import pytest

from src.services.prompts import SYSTEM_PROMPT, build_user_prompt


def test_escalate_default_is_false() -> None:
    """Главный инвариант: в промпте явно зафиксирован дефолт false."""
    assert "escalate=false" in SYSTEM_PROMPT


def test_four_escalation_triggers_present() -> None:
    """Перечислены четыре триггера: (a), (b), (c), (d)."""
    assert "(a)" in SYSTEM_PROMPT
    assert "(b)" in SYSTEM_PROMPT
    assert "(c)" in SYSTEM_PROMPT
    assert "(d)" in SYSTEM_PROMPT


@pytest.mark.parametrize(
    "marker",
    [
        "«суд»",
        "«иск»",
        "«прокуратура»",
        "«Роспотребнадзор»",
        "«юрист»",
        "«адвокат»",
        "«компенсация»",
        "«моральный",
    ],
)
def test_legal_trigger_markers_present(marker: str) -> None:
    """Триггер (b) содержит явные слова-маркеры юридической угрозы.

    Регресс на баг: раньше формулировка была размытой и модель
    расширительно эскалировала сбои на проде.
    """
    assert marker in SYSTEM_PROMPT


def test_technical_example_is_not_escalated() -> None:
    """Пример '502 → processed' зафиксирован: сбой на проде — рутина."""
    assert "Сайт выдаёт 502" in SYSTEM_PROMPT


def test_language_rule_present() -> None:
    """Регресс: правило языка зафиксировано, иначе gpt-4o-mini мешает
    русский с английским (например, 'не arrived') для англоязычных входов.
    """
    assert "ПРАВИЛО ЯЗЫКА" in SYSTEM_PROMPT
    assert "ВСЕГДА пиши на РУССКОМ" in SYSTEM_PROMPT


def test_language_example_present() -> None:
    """Пример англоязычного входа зафиксирован в few-shot."""
    assert "Hello, my order" in SYSTEM_PROMPT


def test_spam_trigger_requires_escalation() -> None:
    """Регресс на баг: спам ОБЯЗАН эскалироваться.

    Ранее модель распознавала спам (category=other, next_action='игнорировать'),
    но ставила escalate=false — потому что трактовала escalate как
    «передать оператору разбираться». Правило (c) теперь явно требует
    escalate=true с объяснением семантики.
    """
    assert "ОБЯЗАТЕЛЬНО" in SYSTEM_PROMPT
    assert "Пометить как спам" in SYSTEM_PROMPT


def test_spam_example_has_escalate_true() -> None:
    """Few-shot пример спама содержит escalate=TRUE."""
    assert "Купите базу email за 500 руб" in SYSTEM_PROMPT
    assert "TRUE" in SYSTEM_PROMPT


def test_json_only_format_required() -> None:
    """Модель обязана вернуть только JSON, без markdown."""
    assert "ТОЛЬКО валидный JSON" in SYSTEM_PROMPT
    assert "markdown" in SYSTEM_PROMPT.lower()


def test_few_shot_examples_present() -> None:
    """Few-shot примеры есть в обоих блоках."""
    assert "ПРИМЕРЫ (escalate=false)" in SYSTEM_PROMPT
    assert "ПРИМЕРЫ (escalate=true)" in SYSTEM_PROMPT


def test_user_prompt_wraps_text() -> None:
    prompt = build_user_prompt("  Не пришёл счёт  ")
    assert "Не пришёл счёт" in prompt
    assert "  Не пришёл счёт  " not in prompt