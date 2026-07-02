import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL')
    GENAPI_KEY = os.getenv('GENAPI_KEY')
    GENAPI_URL = os.getenv('GENAPI_URL', 'https://api.genapi.ai/v1')
    TELEGRAM_API_BASE_URL = os.getenv('TELEGRAM_API_BASE_URL', '')

    # Модели и параметры
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')
    DEFAULT_TEMPERATURE = float(os.getenv('DEFAULT_TEMPERATURE', 0.7))
    DEFAULT_MAX_TOKENS = int(os.getenv('DEFAULT_MAX_TOKENS', 1000))
    CONTEXT_LIMIT = int(os.getenv('CONTEXT_LIMIT', 10))

    # Память (для агента)
    MEMORY_FILE = os.getenv('MEMORY_FILE', 'memory.json')

    # Векторная БД (опционально)
    EMBED_MODEL = os.getenv('EMBED_MODEL', 'text-embedding-3-small')
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 500))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 50))
    VECTOR_DB_PATH = os.getenv('VECTOR_DB_PATH', './chroma_db')
    TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS', 5))
    EMBED_BATCH_SIZE = int(os.getenv('EMBED_BATCH_SIZE', 100))
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 20))

    @classmethod
    def validate(cls):
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не задан в .env")
        if not cls.OPENAI_API_KEY and not cls.GENAPI_KEY:
            raise ValueError("Не указан ни OPENAI_API_KEY, ни GENAPI_KEY")