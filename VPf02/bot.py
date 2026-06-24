#!/usr/bin/env python3
"""
Telegram бот с AI (OpenAI/GenAPI) и контекстом.
Использует увеличенные таймауты через builder.
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import Config
from context_manager import ContextManager
from api_client import create_api_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

config = Config()
config.validate()

context_manager = ContextManager(limit=config.CONTEXT_LIMIT)
api_client = create_api_client(config)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я бот с поддержкой контекста. Просто задавай вопросы, "
        "а я запоминаю диалог. Для очистки контекста используй /reset."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    context_manager.clear_context(user_id)
    await update.message.reply_text("Контекст очищен. Начинаем заново!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text

    context_manager.add_message(user_id, "user", user_text)
    history = context_manager.get_full_history(user_id)

    try:
        logger.info(f"User {user_id} request: {user_text}")
        response_data = api_client.generate_response(
            messages=history,
            temperature=config.DEFAULT_TEMPERATURE,
            max_tokens=config.DEFAULT_MAX_TOKENS,
            model=config.DEFAULT_MODEL
        )
        reply = response_data['content']
        usage = response_data.get('usage', {})
        logger.info(f"Response tokens: {usage}")

        context_manager.add_message(user_id, "assistant", reply)
        await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Error processing user {user_id}: {e}")
        await update.message.reply_text("Извините, произошла ошибка при обработке запроса. Попробуйте позже.")


def main() -> None:
    builder = Application.builder().token(config.BOT_TOKEN)
    if config.TELEGRAM_API_BASE_URL:
        builder = builder.base_url(config.TELEGRAM_API_BASE_URL)
        logger.info(f"Используется базовый URL: {config.TELEGRAM_API_BASE_URL}")
    else:
        logger.info("Используется стандартный базовый URL (https://api.telegram.org)")

    # Увеличиваем таймауты
    builder = builder.connect_timeout(60.0).read_timeout(120.0)

    application = builder.build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started (python-telegram-bot)")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()