"""Модуль конфигурации: загрузка переменных окружения."""
import os
from dotenv import load_dotenv

# Загружаем .env из корня проекта
load_dotenv()

class Config:
    """Хранилище настроек."""
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    VK_BOT_TOKEN: str = os.getenv("VK_BOT_TOKEN", "")

    @classmethod
    def validate(cls) -> None:
        """Проверяет, что все необходимые ключи заданы."""
        if not cls.OPENWEATHER_API_KEY:
            raise ValueError("OPENWEATHER_API_KEY не найден в .env")
        if not cls.VK_BOT_TOKEN:
            raise ValueError("VK_BOT_TOKEN не найден в .env")