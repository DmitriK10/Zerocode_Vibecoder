import logging
import httpx
from app.config import settings

logger = logging.getLogger("OrderPort")

class GPTProxyService:
    def __init__(self, http_client: httpx.AsyncClient = None):
        self.client = http_client or httpx.AsyncClient(
            base_url=settings.OPENAI_API_BASE,
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            timeout=30.0
        )
        # Проверка: разрешена только модель gpt-3.5-turbo-16k
        if settings.OPENAI_MODEL != "gpt-3.5-turbo-16k":
            raise ValueError("Model must be gpt-3.5-turbo-16k")
        self.model = settings.OPENAI_MODEL

    async def generate_response(self, prompt: str, max_tokens: int = None) -> str:
        if max_tokens is None:
            max_tokens = settings.OPENAI_MAX_TOKENS

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }

        logger.info(f"Sending request to GPT proxy with model {self.model}")
        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            logger.debug("GPT response received successfully")
            return content
        except httpx.HTTPStatusError as e:
            logger.error(f"GPT proxy HTTP error: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"GPT proxy error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Unexpected error in GPT service: {str(e)}")
            raise RuntimeError(f"Unexpected error in GPT service: {str(e)}")

    async def close(self):
        await self.client.aclose()