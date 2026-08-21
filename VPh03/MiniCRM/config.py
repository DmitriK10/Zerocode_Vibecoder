"""
Конфигурация приложения с загрузкой переменных из .env и проверкой ограничений.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from logger import logger

# Загружаем .env из корня проекта
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)

# Защищённая папка для токена
HOME_DIR = Path.home()
CRM_DIR = HOME_DIR / ".crm"
CRM_DIR.mkdir(exist_ok=True)
TOKEN_PATH = CRM_DIR / "token.pickle"

class Settings:
    """Настройки приложения."""

    # Google
    GOOGLE_SERVICE_ACCOUNT_FILE: str = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_FILE",
        str(BASE_DIR / "google_integration" / "credentials_service.json")
    )
    GOOGLE_OAUTH_CLIENT_FILE: str = os.getenv(
        "GOOGLE_OAUTH_CLIENT_FILE",
        str(BASE_DIR / "google_integration" / "client_secret.json")
    )
    GOOGLE_TOKEN_PICKLE_FILE: str = str(TOKEN_PATH)  # новый путь
    GOOGLE_FOLDER_ID: str = os.getenv("GOOGLE_FOLDER_ID", "")

    # OpenAI (ограничение модели)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-16k")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Бэкенд
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    # Режим
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    def validate(self):
        """Проверяет допустимые значения."""
        allowed_models = ["gpt-3.5-turbo-16k", "gpt-3.5-turbo"]
        if self.OPENAI_MODEL not in allowed_models:
            raise ValueError(
                f"OPENAI_MODEL must be one of {allowed_models}, got {self.OPENAI_MODEL}"
            )
        if not self.GOOGLE_FOLDER_ID:
            raise ValueError("GOOGLE_FOLDER_ID is not set in .env")
        logger.info("Конфигурация загружена успешно")
        return True

settings = Settings()
settings.validate()