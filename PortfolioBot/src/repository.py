import json
from typing import List, Dict, Any
from src.interfaces import ProjectRepositoryInterface

class JsonProjectRepository(ProjectRepositoryInterface):
    def __init__(self, file_path: str):
        self._file_path = file_path

    def get_projects(self) -> List[Dict[str, Any]]:
        try:
            with open(self._file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return []
                return data.get("projects", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []