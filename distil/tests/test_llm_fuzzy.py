"""Tests for :mod:`app.llm.fuzzy`."""

from __future__ import annotations

import pytest

from app.llm.fuzzy import (
    DEFAULT_QUOTE_THRESHOLD,
    normalize_for_match,
    verify_source_quote,
)


def test_normalize_collapses_whitespace_and_quotes() -> None:
    raw = "  Привет,\u00a0мир!   «Кавычки»   —   и тире.  "
    assert normalize_for_match(raw) == 'привет, мир! "кавычки" - и тире.'


def test_exact_substring_is_confirmed_with_score_one() -> None:
    source = "Нужно до пятницы подготовить отчёт по продажам."
    quote = "до пятницы подготовить отчёт"
    confirmed, score = verify_source_quote(quote, source)
    assert confirmed is True
    assert score == pytest.approx(1.0)


def test_case_and_whitespace_insensitive_match() -> None:
    source = "Please, prepare the report by Friday."
    quote = "PREPARE   the report"
    confirmed, score = verify_source_quote(quote, source)
    assert confirmed is True
    assert score == pytest.approx(1.0)


def test_fuzzy_match_above_threshold() -> None:
    source = "Не забудь согласовать бюджет на третий квартал."
    quote = "согласовать бюджет на третий квартал"  # minus leading word
    confirmed, score = verify_source_quote(quote, source)
    assert confirmed is True
    assert score >= DEFAULT_QUOTE_THRESHOLD


def test_hallucinated_quote_is_rejected() -> None:
    source = "Подготовить отчёт по продажам."
    quote = "Уволить всех сотрудников отдела маркетинга"
    confirmed, score = verify_source_quote(quote, source)
    assert confirmed is False
    assert score < DEFAULT_QUOTE_THRESHOLD


def test_short_quote_requires_exact_match() -> None:
    source = "Prepare the report."
    confirmed, score = verify_source_quote("xyz", source)
    assert confirmed is False
    assert score == pytest.approx(0.0)


def test_empty_quote_is_rejected() -> None:
    confirmed, score = verify_source_quote("", "Some text.")
    assert confirmed is False
    assert score == pytest.approx(0.0)


def test_invalid_threshold_raises() -> None:
    with pytest.raises(ValueError, match="threshold"):
        verify_source_quote("quote", "source", threshold=0.0)
    with pytest.raises(ValueError, match="threshold"):
        verify_source_quote("quote", "source", threshold=1.5)