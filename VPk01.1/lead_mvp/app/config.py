from pathlib import Path

# Корневая директория проекта (там, где лежит этот файл)
BASE_DIR = Path(__file__).parent.parent

# Путь к файлу SQLite (абсолютный)
DB_PATH = BASE_DIR / "leads.db"

# Путь к логу событий
EVENTS_LOG_PATH = BASE_DIR / "events.log"