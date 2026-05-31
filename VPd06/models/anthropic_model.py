from anthropic import Anthropic
from typing import List, Dict
import httpx
from config import Config
from models.base import BaseAIModel

class AnthropicReasoningModel(BaseAIModel):
    def __init__(self):
        # Используем исправленный base_url без /v1
        self.client = Anthropic(
            api_key=Config.PROXY_API_KEY,
            base_url=Config.ANTHROPIC_BASE_URL,
            timeout=httpx.Timeout(Config.REQUEST_TIMEOUT)
        )
        self.model_name = Config.ANTHROPIC_MODEL
        self.thinking_budget = Config.THINKING_BUDGET_TOKENS
    
    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        # Извлекаем системный промпт
        system_prompt = None
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        try:
            # Полезная отладочная информация (можно закомментировать)
            print(f"[DEBUG] Запрос к Anthropic API: base_url={Config.ANTHROPIC_BASE_URL}, model={self.model_name}")
            
            response = self.client.messages.create(
                model=self.model_name,
                messages=anthropic_messages,
                system=system_prompt,
                max_tokens=4096,
                thinking={
                    "type": "enabled",
                    "budget_tokens": self.thinking_budget
                },
                temperature=0.7
            )
            
            # Обработка ответа
            output_text = ""
            thinking_text = ""
            for block in response.content:
                if block.type == "thinking":
                    thinking_text += block.thinking + "\n"
                elif block.type == "text":
                    output_text += block.text
            
            if thinking_text.strip():
                print("\n[РАЗМЫШЛЕНИЯ МОДЕЛИ]:")
                print(thinking_text.strip())
                print("[КОНЕЦ РАЗМЫШЛЕНИЙ]\n")
            
            if hasattr(response, 'usage'):
                print(f"[INFO] Токены: input={response.usage.input_tokens}, output={response.usage.output_tokens}")
            
            return output_text.strip()
        
        except Exception as e:
            # Расширенная диагностика для 404
            error_msg = str(e)
            if "404" in error_msg:
                raise RuntimeError(
                    f"Ошибка 404: эндпоинт не найден.\n"
                    f"Проверьте:\n"
                    f"1. Ваш ANTHROPIC_BASE_URL = '{Config.ANTHROPIC_BASE_URL}' (должен быть без /v1 на конце).\n"
                    f"2. Модель '{self.model_name}' доступна через ProxyAPI (список моделей: https://proxyapi.ru/docs).\n"
                    f"3. Попробуйте другую модель: claude-3-5-sonnet-20241022, claude-3-opus-20240229.\n"
                    f"Исходная ошибка: {error_msg}"
                )
            else:
                raise RuntimeError(f"Ошибка при запросе к Anthropic модели: {error_msg}")
    
    def get_model_info(self) -> str:
        return f"Думающая модель {self.model_name} (reasoning) через ProxyAPI. Бюджет размышлений: {self.thinking_budget} токенов."