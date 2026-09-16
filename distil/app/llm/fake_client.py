"""Deterministic in-memory LLM client for tests.

Public test API (no need to touch private attributes):

* :meth:`enqueue` — push a raw JSON string onto the FIFO queue.
* :meth:`set_response_for` — map an exact input text to a response.
* :meth:`fail_next` — schedule an exception to be raised on the next call.
* :meth:`reset` — clear queue, map, error and recorded calls.
* :attr:`calls` — read-only tuple of recorded calls.
* :attr:`remaining_responses` — how many queued responses are left.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.llm.protocol import LLMRequest, LLMResponse

_EMPTY_ACTIONS_JSON = '{"actions": []}'


@dataclass(frozen=True, slots=True)
class LLMCall:
    """Recorded call — useful for assertions in tests."""

    text: str
    model: str


class FakeLLMClient:
    """Test double for :class:`LLMClientProtocol`."""

    def __init__(
        self,
        responses: list[str] | None = None,
        *,
        response_map: dict[str, str] | None = None,
        default_response: str | None = None,
        error: Exception | None = None,
        duration_ms: int = 5,
        model: str = "gpt-4o-mini",
    ) -> None:
        self._responses: list[str] = list(responses or [])
        self._response_map: dict[str, str] = dict(response_map or {})
        self._default_response: str = default_response or _EMPTY_ACTIONS_JSON
        self._error: Exception | None = error
        self._duration_ms: int = duration_ms
        self._model: str = model
        self._calls: list[LLMCall] = []
        self._error_raised: bool = False

    # -- Public test API -------------------------------------------------

    def enqueue(self, raw_json: str) -> None:
        """Push a raw JSON string onto the FIFO queue."""
        self._responses.append(raw_json)

    def set_response_for(self, text: str, raw_json: str) -> None:
        """Map an exact input text to a canned response."""
        self._response_map[text] = raw_json

    def fail_next(self, error: Exception) -> None:
        """Schedule ``error`` to be raised on the next call only."""
        self._error = error
        self._error_raised = False

    def reset(self) -> None:
        """Clear queue, map, error and recorded calls."""
        self._responses.clear()
        self._response_map.clear()
        self._error = None
        self._error_raised = False
        self._calls.clear()

    # -- Properties ------------------------------------------------------

    @property
    def calls(self) -> tuple[LLMCall, ...]:
        return tuple(self._calls)

    @property
    def remaining_responses(self) -> int:
        return len(self._responses)

    # -- Protocol --------------------------------------------------------

    async def extract_actions(self, request: LLMRequest) -> LLMResponse:
        self._calls.append(LLMCall(text=request.text, model=self._model))

        if self._error is not None and not self._error_raised:
            self._error_raised = True
            raise self._error

        if request.text in self._response_map:
            raw = self._response_map[request.text]
        elif self._responses:
            raw = self._responses.pop(0)
        else:
            raw = self._default_response

        return LLMResponse(
            raw_json=raw,
            model=self._model,
            duration_ms=self._duration_ms,
        )