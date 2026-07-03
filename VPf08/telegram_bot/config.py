import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    TELEGRAM_API_BASE_URL = os.getenv('TELEGRAM_API_BASE_URL', '')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL')
    MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', 'http://127.0.0.1:8000')

    # Прокси для Telegram (если используется)
    PROXY_HOST = os.getenv('PROXY_HOST', '')
    PROXY_PORT = int(os.getenv('PROXY_PORT', 0)) if os.getenv('PROXY_PORT') else None
    PROXY_TYPE = os.getenv('PROXY_TYPE', 'http')

    @classmethod
    def validate(cls):
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не задан")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY не задан")
        if not cls.MCP_SERVER_URL:
            raise ValueError("MCP_SERVER_URL не задан")
        if cls.PROXY_HOST and cls.PROXY_PORT is None:
            raise ValueError("Если задан PROXY_HOST, нужно указать PROXY_PORT")