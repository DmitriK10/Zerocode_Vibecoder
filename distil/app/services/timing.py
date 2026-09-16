"""Small timing helper used by services when recording ``duration_ms``."""

from __future__ import annotations

import time


def now_monotonic() -> float:
    """Return a monotonic clock reading suitable for duration measurement."""
    return time.perf_counter()


def elapsed_ms(started: float) -> int:
    """Return milliseconds elapsed since ``started`` (always >= 0)."""
    delta = (time.perf_counter() - started) * 1000.0
    return max(0, int(delta))