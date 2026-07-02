#!/usr/bin/env python3
"""
Telegram бот с AI-агентом (инструменты: поиск, погода, крипта, валюты, QR, файлы, команды).
"""
import logging
import os
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import Config
from agent import run_agent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

config = Config()
config.validate()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 Привет! Я AI-агент с инструментами:\n"
        "🔍 Поиск в интернете\n"
        "🌤 Погода в любом городе\n"
        "💰 Курс криптовалют (Bitcoin, Ethereum и др.)\n"
        "💱 Курс обычных валют (USD, EUR, RUB и др.)\n"
        "📱 Генерация QR-кодов из текста\n"
        "📁 Чтение/запись файлов\n"
        "💻 Выполнение команд (ls, pwd, echo, whoami, date, uptime)\n\n"
        "Просто задавай вопросы, я сам решу, какой инструмент использовать.\n"
        "Для очистки истории используй /reset."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    from memory import FileChatMessageHistory
    history = FileChatMessageHistory(config.MEMORY_FILE, str(user_id))
    history.clear()
    await update.message.reply_text("🧹 История диалога очищена. Начинаем заново!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text

    try:
        logger.info(f"User {user_id} request: {user_text}")
        reply = run_agent(user_text, str(user_id))
        logger.info(f"Response: {reply}")

        # Проверяем, есть ли в ответе путь к .png файлу (QR-код)
        match = re.search(r'`([^`]+\.png)`', reply)
        if match:
            file_path = match.group(1)
            logger.info(f"Found file path: {file_path}")
            if os.path.exists(file_path):
                try:
                    # Отправляем файл как фото (для наглядности)
                    with open(file_path, 'rb') as f:
                        await update.message.reply_photo(
                            photo=f,
                            caption="✅ QR-код сгенерирован!"
                        )
                    logger.info(f"File sent: {file_path}")
                    # Удаляем файл после отправки (опционально)
                    # os.remove(file_path)
                    return
                except Exception as e:
                    logger.error(f"Error sending file: {e}")
                    # Если не удалось отправить файл, показываем путь текстом
                    await update.message.reply_text(reply)
                    return
            else:
                logger.warning(f"File not found: {file_path}")
                # Файл не найден – отправляем текст
                await update.message.reply_text(reply)
                return

        # Обычный текстовый ответ
        if len(reply) > 4096:
            for chunk in [reply[i:i+4096] for i in range(0, len(reply), 4096)]:
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Error processing user {user_id}: {e}")
        await update.message.reply_text("❌ Извините, произошла ошибка. Попробуйте позже.")


def main() -> None:
    builder = Application.builder().token(config.BOT_TOKEN)
    if config.TELEGRAM_API_BASE_URL:
        builder = builder.base_url(config.TELEGRAM_API_BASE_URL)
        logger.info(f"Используется базовый URL: {config.TELEGRAM_API_BASE_URL}")
    else:
        logger.info("Используется стандартный базовый URL (https://api.telegram.org)")

    builder = builder.connect_timeout(60.0).read_timeout(120.0)

    application = builder.build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started with AI-agent (new tools: exchange rate, QR-code)")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()