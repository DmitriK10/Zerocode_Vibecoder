from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ProjectRepositoryInterface(ABC):
    @abstractmethod
    def get_projects(self) -> List[Dict[str, Any]]:
        pass

class LLMAssistantInterface(ABC):
    @abstractmethod
    def ask(self, prompt: str) -> str:
        pass