import json
import os
from typing import Set

class FSMStorage:
    """Хранилище состояний пользователей с сохранением в JSON."""

    def __init__(self, file_path="fsm_states.json"):
        self.file_path = file_path
        self._awaiting_phone: Set[int] = set()
        self._load()

    def _load(self):
        """Загружает состояния из файла."""
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._awaiting_phone = set(data.get("awaiting_phone", []))

    def _save(self):
        """Сохраняет состояния в файл."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump({"awaiting_phone": list(self._awaiting_phone)}, f, ensure_ascii=False)

    def add_awaiting_phone(self, user_id: int):
        """Добавляет пользователя в состояние ожидания номера."""
        self._awaiting_phone.add(user_id)
        self._save()

    def remove_awaiting_phone(self, user_id: int):
        """Удаляет пользователя из состояния ожидания номера."""
        self._awaiting_phone.discard(user_id)
        self._save()

    def is_awaiting_phone(self, user_id: int) -> bool:
        """Проверяет, находится ли пользователь в состоянии ожидания номера."""
        return user_id in self._awaiting_phone