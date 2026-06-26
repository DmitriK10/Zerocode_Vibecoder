import os
from dotenv import load_dotenv

# Загружаем переменные окружения при импорте
load_dotenv()

class Config:
    """Централизованное хранилище конфигурации приложения."""
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")
    
    try:
        TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
    except ValueError:
        TEMPERATURE = 0.3
    
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    @classmethod
    def validate(cls) -> None:
        """Проверяет наличие обязательных переменных."""
        if not cls.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY не задан. Укажите его в .env или окружении.")