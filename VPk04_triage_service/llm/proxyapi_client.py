import json
import logging
from typing import Any
from openai import AsyncOpenAI
from app.llm.base import LLMClient
from app.core.config import settings
from app.core.exceptions import LLMServiceError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Ты — ассистент службы поддержки. Твоя задача: классифицировать обращение и написать черновик ответа.

Правила:
1. Отвечай строго по входному тексту, не выдумывай факты.
2. Если данных мало, ставь confidence=low и escalate=true.
3. Категория должна быть одной из: billing, support, complaint, other.
4. draft_reply — 1-6 предложений, вежливо и по делу.
5. Ответ должен быть ТОЛЬКО в формате JSON без лишнего текста.
6. JSON должен содержать поля: category, draft_reply, confidence, escalate.

Пример ответа:
{
    "category": "billing",
    "draft_reply": "Здравствуйте! Мы проверим ваш платёж...",
    "confidence": "high",
    "escalate": false
}
"""

class ProxyAPILLMClient(LLMClient):
    def __init__(self, api_key: str, base_url: str, model: str = None):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model or settings.DEFAULT_MODEL
        # Проверяем, что модель разрешена
        if settings.ALLOWED_MODELS and self.model not in settings.ALLOWED_MODELS:
            logger.warning(
                f"Модель {self.model} не в списке разрешённых. Используем DEFAULT_MODEL."
            )
            self.model = settings.DEFAULT_MODEL

    async def triage(self, text: str) -> dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if not content:
                raise LLMServiceError("Пустой ответ от модели")

            data = json.loads(content)

            # Проверка обязательных полей
            required = ["category", "draft_reply", "confidence", "escalate"]
            for field in required:
                if field not in data:
                    raise LLMServiceError(f"Отсутствует поле {field}")

            # Валидация значений
            if data["category"] not in ["billing", "support", "complaint", "other"]:
                data["category"] = "other"
            if data["confidence"] not in ["high", "medium", "low"]:
                data["confidence"] = "low"
            if not isinstance(data["escalate"], bool):
                data["escalate"] = True

            return data

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Ошибка парсинга ответа LLM: {e}")
            raise LLMServiceError("Некорректный формат ответа модели")
        except Exception as e:
            logger.error(f"Ошибка вызова LLM: {e}")
            raise LLMServiceError(f"Ошибка при обращении к LLM: {str(e)}")