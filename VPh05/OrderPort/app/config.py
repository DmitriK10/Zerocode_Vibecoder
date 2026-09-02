import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "ihor_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "secure_password_123")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ihor_db")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    DATABASE_URL_OVERRIDE: str = os.getenv("DATABASE_URL", "")

    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://proxypi.ru/v1")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-16k")
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))

    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

settings = Settings()