import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI / Proxy
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.proxypi.ru/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-16k")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")
PINECONE_INDEX = os.getenv("PINECONE_INDEX_NAME", "assistant-context")
PINECONE_HOST = os.getenv("PINECONE_HOST")

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Weather
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Pinecone namespaces
PINECONE_NAMESPACE_DOCS = "documents"
PINECONE_NAMESPACE_MESSAGES = "user_messages"

# Retrieval
TOP_K_RESULTS = 5

def validate_env():
    """Проверяет наличие всех обязательных переменных окружения."""
    required = [
        "OPENAI_API_KEY", "PINECONE_API_KEY", "TELEGRAM_TOKEN",
        "WEATHER_API_KEY", "PINECONE_INDEX", "PINECONE_HOST"
    ]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise EnvironmentError(
            f"❌ Отсутствуют обязательные переменные окружения: {', '.join(missing)}\n"
            "Проверьте файл .env"
        )