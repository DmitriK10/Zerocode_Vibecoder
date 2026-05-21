"""Главный модуль запуска VK бота."""
import asyncio
from vk_bot.bot import bot
from vk_bot.handlers import register_handlers
from config import Config

if __name__ == "__main__":
    # 1. Проверяем ключи
    Config.validate()
    
    # 2. Асинхронно регистрируем обработчики (временный цикл, который будет закрыт)
    asyncio.run(register_handlers(bot))
    
    # 3. Запускаем бота в синхронном режиме (создаёт свой цикл, конфликта нет)
    print("Бот запущен. Нажмите Ctrl+C для остановки.")
    bot.run_forever()