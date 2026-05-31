from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseAIModel(ABC):
    """Абстрактный класс для всех AI-моделей."""
    
    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Генерирует ответ на основе истории сообщений.
        
        Args:
            messages: список сообщений формата [{"role": "user", "content": "..."}, ...]
        
        Returns:
            Текстовый ответ модели.
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> str:
        """Возвращает информацию о модели (название, тип)."""
        pass