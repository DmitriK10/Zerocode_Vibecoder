import asyncio
import logging
from config import Config
from ai_client import AIClient
from appointment_manager import AppointmentManager
from vk_bot import VKBot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    # Проверка обязательных переменных окружения
    if not Config.VK_TOKEN:
        raise ValueError("❌ VK_TOKEN не задан в .env")
    if not Config.OPENAI_API_KEY:
        raise ValueError("❌ OPENAI_API_KEY не задан в .env")
    if not Config.OPENAI_BASE_URL:
        raise ValueError("❌ OPENAI_BASE_URL не задан в .env")

    ai_client = AIClient(
        api_key=Config.OPENAI_API_KEY,
        model=Config.OPENAI_MODEL,
        api_url=Config.OPENAI_CHAT_URL
    )
    app_manager = AppointmentManager()
    bot = VKBot(
        token=Config.VK_TOKEN,
        ai_client=ai_client,
        app_manager=app_manager
    )
    logger.info("🚀 Бот запущен и ожидает сообщений...")
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")