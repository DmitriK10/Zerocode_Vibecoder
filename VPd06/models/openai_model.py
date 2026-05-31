from openai import OpenAI
from typing import List, Dict
import httpx
from config import Config
from models.base import BaseAIModel

class OpenAIModel(BaseAIModel):
    """Клиент для OpenAI-совместимых моделей через ProxyAPI."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.PROXY_API_KEY,
            base_url=Config.OPENAI_BASE_URL,
            timeout=httpx.Timeout(Config.REQUEST_TIMEOUT)
        )
        self.model_name = Config.OPENAI_MODEL
    
    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            # Оборачиваем исключение в понятное сообщение
            raise RuntimeError(f"Ошибка при запросе к OpenAI модели: {str(e)}")
    
    def get_model_info(self) -> str:
        return f"OpenAI-совместимая модель: {self.model_name} (через ProxyAPI)"