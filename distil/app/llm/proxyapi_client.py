"""ProxyAPI LLM client (proxyapi.ru).

Policy
------
The allowlist of permitted models is provided by the caller (typically
derived from :class:`app.config.Settings.llm_allowed_models`). This is
the SINGLE source of truth for the model policy — there is no separate
hard-coded model check inside the client.

The client:

* Uses the modern OpenAI SDK (``AsyncOpenAI``); the legacy
  ``openai.ChatCompletion`` interface is not supported.
* Sends ``response_format={"type": "json_object"}`` and a low temperature
  to enforce strict JSON output.
* Refuses to start if the configured model is not in the allowlist.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from openai import AsyncOpenAI

from app.llm.exceptions import LLMConfigError, LLMResponseError
from app.llm.prompts import SYSTEM_PROMPT, build_user_message
from app.llm.protocol import LLMRequest, LLMResponse


class ProxyApiLLMClient:
    """Async LLM client backed by proxyapi.ru via the OpenAI SDK."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        allowed_models: list[str],
        temperature: float,
        timeout_seconds: int,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        if not api_key or api_key == "replace-me":
            raise LLMConfigError("LLM_API_KEY is not configured")
        if not base_url:
            raise LLMConfigError("LLM_BASE_URL is not configured")
        if not allowed_models:
            raise LLMConfigError("allowed_models must not be empty")
        if model not in allowed_models:
            raise LLMConfigError(
                f"Model {model!r} is not in the allowlist {allowed_models!r}. "
                "Update LLM_ALLOWED_MODELS in settings to permit a new model."
            )
        if timeout_seconds <= 0:
            raise LLMConfigError("timeout_seconds must be positive")

        self._model = model
        self._temperature = temperature
        self._timeout_seconds = timeout_seconds

        factory = client_factory or AsyncOpenAI
        self._client: Any = factory(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
        )

    @property
    def model(self) -> str:
        return self._model

    async def extract_actions(self, request: LLMRequest) -> LLMResponse:
        """Call the LLM and return its raw JSON string."""
        started = time.perf_counter()
        completion = await self._client.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            response_format={"type": "json_object"},
            timeout=self._timeout_seconds,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_message(request.text)},
            ],
        )
        duration_ms = int((time.perf_counter() - started) * 1000)

        try:
            content = completion.choices[0].message.content
        except (AttributeError, IndexError) as exc:
            raise LLMResponseError(
                "Upstream LLM response has no choices/message content"
            ) from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMResponseError("Upstream LLM returned empty message content")

        return LLMResponse(
            raw_json=content,
            model=self._model,
            duration_ms=duration_ms,
        )