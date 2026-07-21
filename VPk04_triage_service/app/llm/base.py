from abc import ABC, abstractmethod
from typing import Any


class LLMClient(ABC):
    @abstractmethod
    async def triage(self, text: str) -> dict[str, Any]:
        """
        Возвращает словарь с ключами:
        - category
        - draft_reply
        - confidence
        - escalate
        """
        ...