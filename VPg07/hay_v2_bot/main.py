from config import validate_env

# Проверяем .env перед импортом бота
validate_env()

from bot.telegram_bot import bot

if __name__ == "__main__":
    bot.infinity_polling()