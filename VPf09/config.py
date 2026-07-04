import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    TELEGRAM_API_BASE_URL = os.getenv("TELEGRAM_API_BASE_URL")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    CONTEXT_LIMIT = int(os.getenv("CONTEXT_LIMIT", 5))

    # Путь к базе данных SQLite для истории
    DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "history.db"))

    @classmethod
    def validate(cls):
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не задан")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY не задан")
        if not cls.OPENAI_BASE_URL:
            raise ValueError("OPENAI_BASE_URL не задан")