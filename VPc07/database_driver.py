from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

class DatabaseDriver(ABC):
    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def execute(self, query: str, params: Optional[tuple] = None) -> None:
        pass

    @abstractmethod
    def select(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        pass

    @abstractmethod
    def update(self, table: str, data: Dict[str, Any], condition: str, params: tuple) -> None:
        pass

    @abstractmethod
    def delete(self, table: str, condition: str, params: tuple) -> None:
        pass

    @abstractmethod
    def create_table_from_model(self, model_class: type) -> bool:
        pass