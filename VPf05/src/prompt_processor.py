import logging
from typing import Dict, Any, Iterator
from .openai_client import OpenAIClientInterface

logger = logging.getLogger(__name__)

class PromptProcessor:
    """
    Формирует системный и пользовательский промпты на основе шаблона,
    отправляет их в OpenAI и возвращает ответ (обычный или потоковый).
    """
    
    def __init__(self, openai_client: OpenAIClientInterface):
        self.openai_client = openai_client

    def _build_messages(self, prompt_template: Dict[str, Any], user_input: str) -> list:
        role = prompt_template.get("role", "Ты – полезный ассистент.")
        context = prompt_template.get("context", "")
        system_content = f"{role}\n\nКонтекст: {context}"
        
        user_content = f"Задача: {user_input}"
        structure = prompt_template.get("structure", {})
        if structure:
            format_desc = "Формат ответа должен быть структурирован следующим образом:\n"
            for comp in structure.get("components", []):
                format_desc += f"- {comp.get('name')}: {comp.get('description')}\n"
            user_content += f"\n\n{format_desc}"
        
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]

    def process(self, prompt_template: Dict[str, Any], user_input: str, temperature: float = 0.7) -> str:
        messages = self._build_messages(prompt_template, user_input)
        logger.debug(f"Системное сообщение: {messages[0]['content'][:100]}...")
        return self.openai_client.generate_response(messages, temperature)

    def process_stream(self, prompt_template: Dict[str, Any], user_input: str, temperature: float = 0.7) -> Iterator[str]:
        messages = self._build_messages(prompt_template, user_input)
        logger.debug("Запуск потоковой обработки")
        yield from self.openai_client.stream_response(messages, temperature)