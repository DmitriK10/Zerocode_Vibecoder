import os
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Iterator, Optional
import openai

logger = logging.getLogger(__name__)

class OpenAIClientInterface(ABC):
    """Абстракция для клиента OpenAI."""

    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        pass

    @abstractmethod
    def stream_response(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> Iterator[str]:
        """Генерирует ответ по частям (потоковый режим)."""
        pass


class OpenAIClient(OpenAIClientInterface):
    """Реализация клиента с поддержкой потокового режима и настраиваемым base_url."""

    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        if model is None:
            model = "openai/gpt-4o-mini"

        # Определяем base_url:
        # 1. Если передан явно – используем его.
        # 2. Иначе читаем из переменных окружения (сначала OPENAI_BASE_URL, потом GENAPI_URL).
        # 3. Если ничего не задано – используем стандартный URL OpenAI.
        if base_url is None:
            base_url = (
                os.getenv("OPENAI_BASE_URL")
                or os.getenv("GENAPI_URL")
                or "https://api.openai.com/v1"
            )
        else:
            # Если передан явно, но равен пустой строке – тоже используем стандартный
            if base_url.strip() == "":
                base_url = "https://api.openai.com/v1"

        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        logger.info(f"Инициализирован клиент с моделью {self.model}, base_url={base_url}")

    def generate_response(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        try:
            logger.debug(f"Отправка запроса (без stream) к модели {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=False
            )
            content = response.choices[0].message.content
            logger.info(f"Получен ответ длиной {len(content)} символов")
            return content
        except Exception as e:
            logger.error(f"Ошибка при обращении к OpenAI: {e}", exc_info=True)
            raise RuntimeError(f"Ошибка при обращении к OpenAI: {e}")

    def stream_response(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> Iterator[str]:
        try:
            logger.debug(f"Отправка потокового запроса к модели {self.model}")
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            logger.info("Потоковый ответ завершён")
        except Exception as e:
            logger.error(f"Ошибка при потоковом обращении к OpenAI: {e}", exc_info=True)
            raise RuntimeError(f"Ошибка при потоковом обращении к OpenAI: {e}")