import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import router

# Настройка логирования (для отладки)
logging.basicConfig(level=logging.INFO)

async def main():
    # Создаём экземпляр бота
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Регистрируем роутер с обработчиками
    dp.include_router(router)
    
    # Запускаем поллинг (бот начинает слушать сообщения)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())