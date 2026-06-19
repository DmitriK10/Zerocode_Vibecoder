import json
from typing import Dict, Any

class PlanLoader:
    """Загружает JSON-план из указанного файла."""
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> Dict[str, Any]:
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)