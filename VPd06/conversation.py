import json
import os
from typing import List, Dict
from config import Config

class ConversationManager:
    """
    Управляет историей сообщений: загрузка из файла, сохранение, добавление.
    """
    
    def __init__(self, history_file: str = None):
        self.history_file = history_file or Config.HISTORY_FILE
        self.messages: List[Dict[str, str]] = []
        self._load_history()
    
    def _load_history(self):
        """Загружает историю из JSON-файла (если существует)."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.messages = json.load(f)
                print(f"[INFO] История загружена из {self.history_file} ({len(self.messages)} сообщений)")
            except Exception as e:
                print(f"[WARN] Не удалось загрузить историю: {e}")
                self.messages = []
        else:
            print("[INFO] Файл истории не найден, начинаем новый диалог.")
            # Добавляем системный промпт (по желанию)
            self.messages.append({
                "role": "system",
                "content": "Ты полезный ассистент. Отвечай на русском языке, будь вежливым и информативным."
            })
    
    def save_history(self):
        """Сохраняет текущую историю в JSON-файл."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=2)
            print(f"[INFO] История сохранена в {self.history_file}")
        except Exception as e:
            print(f"[ERROR] Не удалось сохранить историю: {e}")
    
    def add_user_message(self, text: str):
        """Добавляет сообщение пользователя в историю."""
        self.messages.append({"role": "user", "content": text})
    
    def add_assistant_message(self, text: str):
        """Добавляет ответ ассистента в историю."""
        self.messages.append({"role": "assistant", "content": text})
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Возвращает всю историю сообщений."""
        return self.messages.copy()
    
    def clear_history(self):
        """Очищает историю, оставляя только системный промпт."""
        system_messages = [msg for msg in self.messages if msg["role"] == "system"]
        self.messages = system_messages if system_messages else [
            {"role": "system", "content": "Ты полезный ассистент. Отвечай на русском языке."}
        ]
        self.save_history()