import os

# Токен вашего бота (получите у BotFather)
BOT_TOKEN = "8725452085:AAF8uKILvO0bGz92uvlyope7XAQIUCx7I8k"

# Путь к файлу базы данных (абсолютный)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "tasks.db")

# Папка для временных CSV-файлов
CSV_EXPORT_DIR = os.path.join(BASE_DIR, "exports")
os.makedirs(CSV_EXPORT_DIR, exist_ok=True)