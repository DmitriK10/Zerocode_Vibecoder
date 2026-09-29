import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 1. Динамический абсолютный путь к корню проекта (Best Practice)
# Path(__file__) берет путь к текущему файлу, .parent поднимается на уровень вверх (в корень), 
# .resolve() превращает его в чистый абсолютный путь без относительных элементов.
BASE_DIR = Path(__file__).parent.resolve()

# Добавляем корень проекта в sys.path для корректного импорта модулей (например, src.*)
sys.path.append(str(BASE_DIR))

# 2. Загрузка переменных окружения из файла .env, лежащего рядом с main.py
load_dotenv(BASE_DIR / ".env")

from aiogram import Bot, Dispatcher
from src.repository import JsonProjectRepository
from src.ai_service import ProxyOpenAIClient
from src.bot_handlers import PortfolioBotHandlers, router

async def main():
    # 3. Формирование путей через оператор / (рекомендуемый способ в pathlib)
    json_path = BASE_DIR / "projects.json"
    repository = JsonProjectRepository(str(json_path))
    
    # Безопасное получение ключей. Если их нет в .env, берется заглушка для локальной отладки
    api_key = os.getenv("OPENAI_API_KEY", "dummy_key_for_local_run")
    ai_client = ProxyOpenAIClient(api_key=api_key)
    
    handlers = PortfolioBotHandlers(repository, ai_client)
    handlers.register_handlers(router)
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("Критическая ошибка: BOT_TOKEN не найден в файле .env")
        
    print(f"DEBUG: Инициализация бота. Токен начинается с: {bot_token[:15]}...")
    print(f"DEBUG: Рабочая директория (BASE_DIR): {BASE_DIR}")
    
    bot = Bot(token=bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    
    print("✅ Бот успешно инициализирован! Запускаю polling...")
    await dp.start_polling(bot)

# 4. Корректная точка входа (исправлено с "if name == 'main':")
if __name__ == "__main__":
    # В Windows для asyncio рекомендуется использовать WindowsSelectorEventLoopPolicy 
    # при работе с aiogram и прокси, чтобы избежать ошибок с прокси-соединениями
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())