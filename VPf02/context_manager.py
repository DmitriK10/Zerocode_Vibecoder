from typing import Dict, List, Optional

class ContextManager:
    def __init__(self, limit: int = 10):
        self._contexts: Dict[int, List[Dict[str, str]]] = {}
        self.limit = limit

    def get_context(self, user_id: int) -> List[Dict[str, str]]:
        return self._contexts.get(user_id, []).copy()

    def add_message(self, user_id: int, role: str, content: str):
        if user_id not in self._contexts:
            self._contexts[user_id] = []
        self._contexts[user_id].append({"role": role, "content": content})
        if len(self._contexts[user_id]) > self.limit:
            self._contexts[user_id] = self._contexts[user_id][-self.limit:]

    def clear_context(self, user_id: int):
        if user_id in self._contexts:
            self._contexts[user_id] = []

    def get_full_history(self, user_id: int) -> List[Dict[str, str]]:
        return self._contexts.get(user_id, [])

    def set_context(self, user_id: int, context: List[Dict[str, str]]):
        self._contexts[user_id] = context[-self.limit:] if context else []