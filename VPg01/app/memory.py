from typing import List, Dict

class ShortTermMemory:
    def __init__(self, max_size: int = 20):
        self.max_size = max_size
        self.messages: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_size:
            self.messages = self.messages[-self.max_size:]

    def get_messages(self) -> List[Dict[str, str]]:
        return self.messages.copy()

    def clear(self) -> None:
        self.messages.clear()