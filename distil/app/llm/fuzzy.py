"""Normalisation and fuzzy matching for ``source_quote`` verification.

The model is instructed to return verbatim quotes, but it may still
introduce tiny deviations: case, extra whitespace, typographic vs ASCII
quotes, en/em dashes, or the Russian «ёлочки». Exact ``in`` matching
would therefore produce false ``needs_review`` flags and waste user time.

We normalise both strings and use ``rapidfuzz.fuzz.partial_ratio`` to
find the best alignment of the (short) quote inside the (long) source.
"""

from __future__ import annotations

import re

from rapidfuzz import fuzz

DEFAULT_QUOTE_THRESHOLD: float = 0.85

_WHITESPACE_RE = re.compile(r"\s+")

# Typographic → ASCII normalisation map.
_PUNCT_TRANSLATION = str.maketrans(
    {
        "«": '"',
        "»": '"',
        "„": '"',
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "`": "'",
        "´": "'",
        "–": "-",
        "—": "-",
        "−": "-",
        "\u00a0": " ",  # non-breaking space
        "\u202f": " ",  # narrow no-break space
    }
)


def normalize_for_match(text: str) -> str:
    """Lowercase, collapse whitespace, unify quotes/dashes."""
    lowered = text.lower().translate(_PUNCT_TRANSLATION)
    collapsed = _WHITESPACE_RE.sub(" ", lowered)
    return collapsed.strip()


def verify_source_quote(
    quote: str,
    source: str,
    *,
    threshold: float = DEFAULT_QUOTE_THRESHOLD,
) -> tuple[bool, float]:
    """Return ``(confirmed, score)`` for ``quote`` inside ``source``.

    ``score`` is a float in ``[0.0, 1.0]``. The quote is considered
    confirmed when an exact (normalised) substring match exists, or when
    ``partial_ratio`` is at least ``threshold``.
    """
    if not 0.0 < threshold <= 1.0:
        raise ValueError(f"threshold must be in (0.0, 1.0], got {threshold!r}")

    normalized_quote = normalize_for_match(quote)
    normalized_source = normalize_for_match(source)

    if not normalized_quote:
        return False, 0.0
    if not normalized_source:
        return False, 0.0

    # Fast path: exact normalised substring.
    if normalized_quote in normalized_source:
        return True, 1.0

    # Short quotes (< 5 chars) produce noisy partial ratios — require exact.
    if len(normalized_quote) < 5:
        return False, 0.0

    raw_score = fuzz.partial_ratio(normalized_quote, normalized_source) / 100.0
    return raw_score >= threshold, float(raw_score)