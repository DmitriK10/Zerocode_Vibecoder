"""LLM layer for the Distil project.

Public API:
* ``protocol`` — :class:`LLMClientProtocol` and request/response DTOs.
* ``parser`` — parse raw LLM JSON into validated ``ActionCreate`` items.
* ``prompts`` — system prompt, user message builder, injection detector.
* ``proxyapi_client`` — real client (proxyapi.ru, gpt-4o-mini only).
* ``fake_client`` — deterministic in-memory client for tests.
* ``exceptions`` — typed errors raised by the layer.
"""

from app.llm.exceptions import (
    LLMConfigError,
    LLMError,
    LLMParseError,
    LLMResponseError,
)
from app.llm.fake_client import FakeLLMClient
from app.llm.parser import parse_llm_response
from app.llm.protocol import LLMClientProtocol, LLMRequest, LLMResponse
from app.llm.proxyapi_client import ProxyApiLLMClient

__all__ = [
    "FakeLLMClient",
    "LLMClientProtocol",
    "LLMConfigError",
    "LLMError",
    "LLMParseError",
    "LLMRequest",
    "LLMResponse",
    "LLMResponseError",
    "ProxyApiLLMClient",
    "parse_llm_response",
]