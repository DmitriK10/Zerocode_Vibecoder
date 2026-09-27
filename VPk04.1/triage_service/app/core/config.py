from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Обязательные поля
    OPENAI_API_KEY: str
    
    # Необязательные поля со значениями по умолчанию
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    RATE_LIMIT_PER_MINUTE: int = 10
    DEFAULT_MODEL: str = "gpt-4o-mini"
    ALLOWED_MODELS: str = "gpt-4o-mini"

    # Конфигурация Pydantic V2 (заменяет устаревший class Config)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid"  # Защищает от опечаток в .env
    )

settings = Settings()