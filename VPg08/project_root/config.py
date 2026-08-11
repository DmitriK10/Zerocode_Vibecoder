import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)


class Config:
    """
    Класс конфигурации, загружающий переменные окружения.
    Все атрибуты являются строками, полученными из os.getenv().
    """

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-16k")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")
    PINECONE_HOST = os.getenv("PINECONE_HOST")

    @classmethod
    def validate(cls) -> None:
        """
        Проверяет наличие обязательных переменных окружения.
        Выбрасывает EnvironmentError, если какая-либо переменная отсутствует.
        """
        required = [
            "TELEGRAM_BOT_TOKEN",
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
            "PINECONE_API_KEY",
            "PINECONE_INDEX_NAME",
        ]
        missing = [v for v in required if not getattr(cls, v, None)]
        if missing:
            raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")