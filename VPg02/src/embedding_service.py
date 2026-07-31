import os
from openai import OpenAI

class EmbeddingService:
    """
    Сервис для получения эмбеддингов текста через OpenAI API (через прокси).
    """

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.model = model or os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    def get_embedding(self, text: str) -> list[float]:
        if not text or not isinstance(text, str):
            raise ValueError("Текст должен быть непустой строкой")
        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )
        return response.data[0].embedding