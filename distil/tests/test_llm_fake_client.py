"""Tests for :mod:`app.llm.fake_client`."""

from __future__ import annotations

import pytest

from app.llm.exceptions import LLMError
from app.llm.fake_client import FakeLLMClient
from app.llm.protocol import LLMRequest


async def test_default_response_is_empty_actions() -> None:
    client = FakeLLMClient()
    response = await client.extract_actions(LLMRequest(text="anything"))
    assert response.raw_json == '{"actions": []}'
    assert response.model == "gpt-4o-mini"
    assert len(client.calls) == 1


async def test_responses_queue_is_consumed_fifo() -> None:
    client = FakeLLMClient(responses=['{"actions": []}', '{"actions": [1]}'])
    r1 = await client.extract_actions(LLMRequest(text="first"))
    r2 = await client.extract_actions(LLMRequest(text="second"))
    r3 = await client.extract_actions(LLMRequest(text="third"))

    assert r1.raw_json == '{"actions": []}'
    assert r2.raw_json == '{"actions": [1]}'
    # Queue exhausted → default response.
    assert r3.raw_json == '{"actions": []}'
    assert client.remaining_responses == 0


async def test_response_map_takes_precedence_over_queue() -> None:
    client = FakeLLMClient(
        responses=['{"actions": [99]}'],
        response_map={"mapped": '{"actions": [42]}'},
    )
    mapped = await client.extract_actions(LLMRequest(text="mapped"))
    queued = await client.extract_actions(LLMRequest(text="other"))

    assert mapped.raw_json == '{"actions": [42]}'
    assert queued.raw_json == '{"actions": [99]}'


async def test_error_is_raised_only_once() -> None:
    client = FakeLLMClient(error=LLMError("upstream boom"))
    with pytest.raises(LLMError, match="upstream boom"):
        await client.extract_actions(LLMRequest(text="first"))
    # Second call succeeds (uses default).
    response = await client.extract_actions(LLMRequest(text="second"))
    assert response.raw_json == '{"actions": []}'


async def test_calls_are_recorded() -> None:
    client = FakeLLMClient(model="gpt-4o-mini")
    await client.extract_actions(LLMRequest(text="alpha"))
    await client.extract_actions(LLMRequest(text="beta"))

    assert [c.text for c in client.calls] == ["alpha", "beta"]
    assert all(c.model == "gpt-4o-mini" for c in client.calls)