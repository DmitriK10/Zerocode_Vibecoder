import json
import os
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict

class FileChatMessageHistory(BaseChatMessageHistory):
    """
    Хранит историю сообщений в JSON-файле.
    Для каждого session_id (chat_id) хранится отдельный список.
    """
    def __init__(self, file_path: str, session_id: str):
        self.file_path = file_path
        self.session_id = session_id
        self._messages = []
        self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._messages = messages_from_dict(data.get(self.session_id, []))
        else:
            self._messages = []

    def _save(self):
        # Загружаем все данные, обновляем запись для этого session_id и сохраняем
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}
        data[self.session_id] = messages_to_dict(self._messages)
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @property
    def messages(self):
        return self._messages

    def add_message(self, message: BaseMessage) -> None:
        self._messages.append(message)
        self._save()

    def clear(self) -> None:
        self._messages = []
        self._save()