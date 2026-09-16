"""Abstract LLM client interface (Dependency Inversion).

Services depend on :class:`LLMClientProtocol`, never on a concrete SDK
class. This makes swapping providers (proxyapi.ru, OpenAI, local model)
a matter of wiring one implementation at the composition root.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class LLMRequest:
    """Everything an LLM call needs, fully resolved by the caller.

    Note: the protocol deliberately does NOT take a model name from the
    caller — the client owns the allowlist policy so that no service can
    bypass it.
    """

    text: str


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Raw response from the LLM, plus telemetry."""

    raw_json: str
    model: str
    duration_ms: int


@runtime_checkable
class LLMClientProtocol(Protocol):
    """Async extraction client."""

    async def extract_actions(self, request: LLMRequest) -> LLMResponse:
        ...