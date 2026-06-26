import json
import os
from typing import Dict, Any

class PromptLoader:
    """Загружает промпты из JSON-файлов в указанной директории."""
    
    def __init__(self, prompts_dir: str):
        self.prompts_dir = prompts_dir

    def load_prompt(self, filename: str) -> Dict[str, Any]:
        """Загружает один JSON-файл и возвращает словарь."""
        filepath = os.path.join(self.prompts_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Файл не найден: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_all_prompts(self) -> Dict[str, Dict[str, Any]]:
        """Загружает все JSON-файлы из директории, возвращает словарь {имя_файла: данные}."""
        prompts = {}
        for filename in os.listdir(self.prompts_dir):
            if filename.endswith('.json'):
                try:
                    prompts[filename] = self.load_prompt(filename)
                except Exception as e:
                    print(f"Ошибка загрузки {filename}: {e}")
        return prompts