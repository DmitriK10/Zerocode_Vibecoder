import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Настройки приложения из переменных окружения."""
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://proxyapi.ru/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    MAX_HISTORY_SIZE = int(os.getenv("MAX_HISTORY_SIZE", 20))

    _db_path_env = os.getenv("DB_PATH", "bot_database.db")
    if _db_path_env.startswith("/") or _db_path_env.startswith("C:\\"):
        db_dir = os.path.dirname(_db_path_env)
        if db_dir and not os.path.exists(db_dir):
            DB_PATH = "bot_database.db"
        else:
            DB_PATH = _db_path_env
    else:
        DB_PATH = _db_path_env

    HTTP_PROXY = os.getenv("HTTP_PROXY")
    HTTPS_PROXY = os.getenv("HTTPS_PROXY")
    NO_PROXY = os.getenv("NO_PROXY")

    SYSTEM_PROMPT_TEMPLATE = """Ты полезный AI-ассистент. Отвечай по делу.
Если есть тезисы из базы данных (факты о пользователе), учитывай их в ответе.
Тезисы пользователя:
{theses}
История диалога:
{history}

ОТВЕТ ДОЛЖЕН БЫТЬ В ФОРМАТЕ JSON:
{{
  "theses": ["тезис1", "тезис2", ...],
  "message": "текст ответа пользователю"
}}
Не добавляй ничего кроме JSON. Ответ должен быть валидным JSON.
"""