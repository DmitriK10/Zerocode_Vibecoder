from openai import OpenAI
from typing import List, Dict
import httpx
from config import Config
from models.base import BaseAIModel

class DeepSeekReasoningModel(BaseAIModel):
    """
    Модель DeepSeek R1 через OpenRouter (ProxyAPI).
    Поддерживает reasoning_content – видимые размышления.
    """
    
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.PROXY_API_KEY,
            base_url=Config.REASONING_BASE_URL,
            timeout=httpx.Timeout(Config.REQUEST_TIMEOUT)
        )
        self.model_name = Config.REASONING_MODEL
    
    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7
            )
            
            main_content = response.choices[0].message.content or ""
            # Извлекаем reasoning_content, если есть
            reasoning = getattr(response.choices[0].message, 'reasoning_content', None)
            
            if reasoning:
                print("\n[РАЗМЫШЛЕНИЯ МОДЕЛИ (DeepSeek R1)]:")
                print(reasoning.strip())
                print("[КОНЕЦ РАЗМЫШЛЕНИЙ]\n")
            
            return main_content.strip()
            
        except Exception as e:
            error_msg = str(e)
            if "402" in error_msg or "Insufficient balance" in error_msg:
                raise RuntimeError(
                    f"Недостаточно средств для DeepSeek R1. Пополните баланс на proxyapi.ru\n"
                    f"Ошибка: {error_msg}"
                )
            elif "404" in error_msg:
                raise RuntimeError(
                    f"Модель '{self.model_name}' не найдена. Проверьте REASONING_BASE_URL и REASONING_MODEL в .env\n"
                    f"Ошибка: {error_msg}"
                )
            else:
                raise RuntimeError(f"Ошибка при запросе к DeepSeek модели: {error_msg}")
    
    def get_model_info(self) -> str:
        return f"Думающая модель DeepSeek R1 (reasoning) через OpenRouter/ProxyAPI. Бесплатно (есть лимиты)."