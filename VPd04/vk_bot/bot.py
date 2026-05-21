"""Инициализация VKBottle и создание экземпляра бота."""
from vkbottle import Bot
from config import Config

# Токен группы из .env
bot = Bot(token=Config.VK_BOT_TOKEN)