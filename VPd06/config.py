import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PROXY_API_KEY: str = os.getenv("PROXY_API_KEY", "")
    
    # Базовые URL
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.proxyapi.ru/openai/v1")
    REASONING_BASE_URL: str = os.getenv("REASONING_BASE_URL", "https://api.proxyapi.ru/openrouter/v1")
    ANTHROPIC_BASE_URL: str = os.getenv("ANTHROPIC_BASE_URL", "https://api.proxyapi.ru/anthropic")
    
    # Модели
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    REASONING_MODEL: str = os.getenv("REASONING_MODEL", "deepseek/deepseek-r1")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    
    THINKING_BUDGET_TOKENS: int = int(os.getenv("THINKING_BUDGET_TOKENS", "1500"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "60"))
    HISTORY_FILE: str = os.getenv("HISTORY_FILE", "conversation_history.json")
    
    @classmethod
    def validate(cls) -> bool:
        if not cls.PROXY_API_KEY:
            raise ValueError("PROXY_API_KEY не задан в файле .env")
        return True

Config.validate()