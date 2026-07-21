from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    RATE_LIMIT_PER_MINUTE: int = 10

    # Новые настройки для управления моделями
    DEFAULT_MODEL: str = "gpt-4o-mini"                     # дешёвая модель по умолчанию
    ALLOWED_MODELS: list[str] = [                          # белый список разрешённых
        "gpt-4o-mini",
        "gpt-3.5-turbo",
        "gemini-2.5-flash",
        "claude-haiku-4-5",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()