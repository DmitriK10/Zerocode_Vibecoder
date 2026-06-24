import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL')      # для ProxyAPI
    GENAPI_KEY = os.getenv('GENAPI_KEY')
    GENAPI_URL = os.getenv('GENAPI_URL', 'https://api.genapi.ai/v1')

    # Базовый URL для Telegram API (Cloudflare Worker)
    TELEGRAM_API_BASE_URL = os.getenv('TELEGRAM_API_BASE_URL', '')

    DEFAULT_MODEL = 'gpt-3.5-turbo'   # можно заменить на 'openai/gpt-4o' и т.д.
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 1000
    CONTEXT_LIMIT = 10

    @classmethod
    def validate(cls):
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не задан в .env")
        if not cls.OPENAI_API_KEY and not cls.GENAPI_KEY:
            raise ValueError("Не указан ни OPENAI_API_KEY, ни GENAPI_KEY")