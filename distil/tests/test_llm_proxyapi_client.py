"""Tests for :mod:`app.llm.proxyapi_client`.

The OpenAI SDK is replaced by a minimal fake exposing the modern
``chat.completions.create`` interface, so these tests never hit the
network and never need real credentials.

Model policy
------------
The allowlist passed to the client is the single source of truth. The
client itself does NOT contain a hard-coded model policy.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.llm.exceptions import LLMConfigError, LLMResponseError
from app.llm.protocol import LLMRequest
from app.llm.proxyapi_client import ProxyApiLLMClient

# ------------------------------------------------------------- fake SDK


class _FakeMessage:
    def __init__(self, content: str | None) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str | None) -> None:
        self.message = _FakeMessage(content)


class _FakeCompletionResponse:
    def __init__(self, content: str | None) -> None:
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, content: str | None) -> None:
        self._content = content
        self.last_kwargs: dict[str, Any] | None = None

    async def create(self, **kwargs: Any) -> _FakeCompletionResponse:
        self.last_kwargs = kwargs
        return _FakeCompletionResponse(self._content)


class _FakeChat:
    def __init__(self, completions: _FakeCompletions) -> None:
        self.completions = completions


class FakeAsyncOpenAI:
    """Minimal stand-in for ``openai.AsyncOpenAI``."""

    def __init__(self, content: str | None = '{"actions": []}') -> None:
        self._completions = _FakeCompletions(content)
        self.chat = _FakeChat(self._completions)

    @property
    def last_kwargs(self) -> dict[str, Any] | None:
        return self._completions.last_kwargs


def _factory_for(fake: FakeAsyncOpenAI) -> Any:
    def _factory(**_kwargs: Any) -> FakeAsyncOpenAI:
        return fake

    return _factory


# -------------------------------------------------------------- validation


def test_allowed_model_constructs_ok() -> None:
    client = ProxyApiLLMClient(
        api_key="sk-test",
        base_url="https://api.proxyapi.ru/openai/v1",
        model="gpt-4o-mini",
        allowed_models=["gpt-4o-mini"],
        temperature=0.1,
        timeout_seconds=30,
        client_factory=_factory_for(FakeAsyncOpenAI()),
    )
    assert client.model == "gpt-4o-mini"


def test_custom_model_in_allowlist_constructs_ok() -> None:
    """The allowlist is data-driven; no hard-coded model policy exists."""
    client = ProxyApiLLMClient(
        api_key="sk-test",
        base_url="https://api.proxyapi.ru/openai/v1",
        model="custom-mini",
        allowed_models=["gpt-4o-mini", "custom-mini"],
        temperature=0.1,
        timeout_seconds=30,
        client_factory=_factory_for(FakeAsyncOpenAI()),
    )
    assert client.model == "custom-mini"


def test_missing_api_key_raises_config_error() -> None:
    with pytest.raises(LLMConfigError, match="LLM_API_KEY"):
        ProxyApiLLMClient(
            api_key="",
            base_url="https://api.proxyapi.ru/openai/v1",
            model="gpt-4o-mini",
            allowed_models=["gpt-4o-mini"],
            temperature=0.1,
            timeout_seconds=30,
            client_factory=_factory_for(FakeAsyncOpenAI()),
        )


def test_placeholder_api_key_raises_config_error() -> None:
    with pytest.raises(LLMConfigError, match="LLM_API_KEY"):
        ProxyApiLLMClient(
            api_key="replace-me",
            base_url="https://api.proxyapi.ru/openai/v1",
            model="gpt-4o-mini",
            allowed_models=["gpt-4o-mini"],
            temperature=0.1,
            timeout_seconds=30,
            client_factory=_factory_for(FakeAsyncOpenAI()),
        )


def test_model_outside_allowlist_raises() -> None:
    with pytest.raises(LLMConfigError, match="allowlist"):
        ProxyApiLLMClient(
            api_key="sk-test",
            base_url="https://api.proxyapi.ru/openai/v1",
            model="gpt-4o",
            allowed_models=["gpt-4o-mini"],
            temperature=0.1,
            timeout_seconds=30,
            client_factory=_factory_for(FakeAsyncOpenAI()),
        )


def test_empty_allowlist_raises() -> None:
    with pytest.raises(LLMConfigError, match="allowed_models"):
        ProxyApiLLMClient(
            api_key="sk-test",
            base_url="https://api.proxyapi.ru/openai/v1",
            model="gpt-4o-mini",
            allowed_models=[],
            temperature=0.1,
            timeout_seconds=30,
            client_factory=_factory_for(FakeAsyncOpenAI()),
        )


def test_non_positive_timeout_raises() -> None:
    with pytest.raises(LLMConfigError, match="timeout_seconds"):
        ProxyApiLLMClient(
            api_key="sk-test",
            base_url="https://api.proxyapi.ru/openai/v1",
            model="gpt-4o-mini",
            allowed_models=["gpt-4o-mini"],
            temperature=0.1,
            timeout_seconds=0,
            client_factory=_factory_for(FakeAsyncOpenAI()),
        )


# ------------------------------------------------------------- call shape


async def test_extract_actions_sends_expected_kwargs() -> None:
    fake = FakeAsyncOpenAI(content='{"actions": []}')
    client = ProxyApiLLMClient(
        api_key="sk-test",
        base_url="https://api.proxyapi.ru/openai/v1",
        model="gpt-4o-mini",
        allowed_models=["gpt-4o-mini"],
        temperature=0.1,
        timeout_seconds=30,
        client_factory=_factory_for(fake),
    )

    response = await client.extract_actions(LLMRequest(text="Hello world, do X."))

    assert response.raw_json == '{"actions": []}'
    assert response.model == "gpt-4o-mini"
    assert response.duration_ms >= 0

    assert fake.last_kwargs is not None
    kwargs = fake.last_kwargs
    assert kwargs["model"] == "gpt-4o-mini"
    assert kwargs["temperature"] == 0.1
    assert kwargs["response_format"] == {"type": "json_object"}
    assert kwargs["timeout"] == 30

    messages = kwargs["messages"]
    assert isinstance(messages, list)
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "Hello world" in messages[1]["content"]


async def test_empty_message_content_raises_response_error() -> None:
    fake = FakeAsyncOpenAI(content=None)
    client = ProxyApiLLMClient(
        api_key="sk-test",
        base_url="https://api.proxyapi.ru/openai/v1",
        model="gpt-4o-mini",
        allowed_models=["gpt-4o-mini"],
        temperature=0.1,
        timeout_seconds=30,
        client_factory=_factory_for(fake),
    )

    with pytest.raises(LLMResponseError, match="empty"):
        await client.extract_actions(LLMRequest(text="Hello world, do X."))


async def test_blank_message_content_raises_response_error() -> None:
    fake = FakeAsyncOpenAI(content="   ")
    client = ProxyApiLLMClient(
        api_key="sk-test",
        base_url="https://api.proxyapi.ru/openai/v1",
        model="gpt-4o-mini",
        allowed_models=["gpt-4o-mini"],
        temperature=0.1,
        timeout_seconds=30,
        client_factory=_factory_for(fake),
    )

    with pytest.raises(LLMResponseError, match="empty"):
        await client.extract_actions(LLMRequest(text="Hello world, do X."))