from enum import Enum

class ModelName(str, Enum):
    GPT4O_MINI = "gpt-4o-mini"
    GPT35_TURBO = "gpt-3.5-turbo"
    GEMINI_FLASH = "gemini-2.5-flash"
    CLAUDE_HAIKU = "claude-haiku-4-5"

    @classmethod
    def list_names(cls) -> list[str]:
        return [m.value for m in cls]