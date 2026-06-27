#!/usr/bin/env python3
"""
Telegram бот с короткой и долгой памятью.
Использует python-telegram-bot, OpenAI/GenAPI и ChromaDB.
"""
import asyncio
import logging
import uuid
from pathlib import Path

from telegram import Update, Document
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import Config
from context_manager import ContextManager
from api_client import create_api_client
from vector_memory import VectorMemoryManager
from utils import load_document

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация конфигурации
config = Config()
config.validate()

# Инициализация компонентов
context_manager = ContextManager(limit=config.CONTEXT_LIMIT)
api_client = create_api_client(config)

# Инициализация менеджера векторной памяти
vector_memory = None
if config.OPENAI_API_KEY:
    vector_memory = VectorMemoryManager(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL,
        embed_model=config.EMBED_MODEL,
        db_path=config.VECTOR_DB_PATH,
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        batch_size=config.EMBED_BATCH_SIZE,
    )
    logger.info("Векторная память инициализирована (ChromaDB)")
else:
    logger.warning("Векторная память не доступна: отсутствует OPENAI_API_KEY")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    await update.message.reply_text(
        "👋 Привет! Я бот с короткой и долгой памятью.\n\n"
        "📄 Отправьте мне PDF, TXT или DOCX — я сохраню его в векторную базу (долгая память).\n"
        "💬 Пишите сообщения — я запоминаю последние 10 реплик (короткая память).\n"
        "❓ Задавайте вопросы — я отвечу, используя загруженные документы и историю диалога.\n\n"
        "Команды:\n"
        "/reset — очистить короткую память (историю диалога)\n"
        "/cleardocs — удалить все ваши документы из долгой памяти"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Очищает короткую память пользователя."""
    user_id = update.effective_user.id
    context_manager.clear_context(user_id)
    await update.message.reply_text("🧹 Короткая память (история диалога) очищена.")


async def cleardocs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Очищает долгую память пользователя (удаляет все документы)."""
    user_id = update.effective_user.id
    if not vector_memory:
        await update.message.reply_text("❌ Векторная память не доступна.")
        return
    try:
        vector_memory.clear_user_data(user_id)
        await update.message.reply_text("🗑️ Все ваши документы удалены из векторной памяти.")
    except Exception as e:
        logger.error(f"Ошибка очистки документов пользователя {user_id}: {e}")
        await update.message.reply_text("❌ Не удалось очистить документы. Попробуйте позже.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик загруженных документов (PDF, TXT, DOCX)."""
    user_id = update.effective_user.id
    document: Document = update.message.document

    if not vector_memory:
        await update.message.reply_text("❌ Векторная память не доступна (нет OpenAI API ключа).")
        return

    # Проверка размера файла
    if document.file_size and document.file_size > config.MAX_FILE_SIZE_MB * 1024 * 1024:
        await update.message.reply_text(
            f"⚠️ Файл слишком большой. Максимальный размер: {config.MAX_FILE_SIZE_MB} МБ."
        )
        return

    # Проверка расширения
    file_name = document.file_name or "unknown"
    extension = file_name.split('.')[-1].lower()
    if extension not in ('pdf', 'txt', 'docx', 'doc'):
        await update.message.reply_text("⚠️ Поддерживаются только PDF, TXT и DOCX файлы.")
        return

    try:
        # Скачиваем файл
        file = await document.get_file()
        temp_dir = Path("./temp_uploads") / str(user_id)
        temp_dir.mkdir(parents=True, exist_ok=True)
        file_path = temp_dir / file_name

        await file.download_to_drive(file_path)

        # Извлекаем текст
        text = load_document(str(file_path))
        if not text.strip():
            await update.message.reply_text("⚠️ Не удалось извлечь текст из документа (файл пуст или повреждён).")
            return

        # Индексируем в векторную базу
        doc_id = uuid.uuid4().hex
        chunk_count = vector_memory.add_document(user_id, text, doc_id)

        # Удаляем временный файл
        file_path.unlink(missing_ok=True)

        await update.message.reply_text(
            f"✅ Документ «{file_name}» успешно проиндексирован.\n"
            f"📊 Создано чанков: {chunk_count}\n"
            f"Теперь вы можете задавать вопросы по этому документу."
        )

    except Exception as e:
        logger.error(f"Ошибка при обработке документа от user {user_id}: {e}")
        await update.message.reply_text(f"❌ Ошибка при обработке документа: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Основной обработчик текстовых сообщений (вопросы пользователя)."""
    user_id = update.effective_user.id
    user_text = update.message.text

    # Получаем историю из короткой памяти (без текущего сообщения)
    history = context_manager.get_full_history(user_id)

    # Получаем контекст из векторной памяти (если доступна)
    vector_context = []
    if vector_memory:
        try:
            vector_context = vector_memory.retrieve_context(
                user_id,
                user_text,
                top_k=config.TOP_K_RESULTS
            )
        except Exception as e:
            logger.error(f"Ошибка получения контекста из векторной памяти: {e}")

    # Формируем системное сообщение с инструкцией и контекстом
    system_content = (
        "Ты — полезный ассистент. Отвечай на вопросы пользователя, используя предоставленный контекст из документов, "
        "если он релевантен. Если контекст пуст или не помогает, используй свои общие знания и историю диалога. "
        "Не выдумывай факты, которых нет в контексте."
    )

    if vector_context:
        context_text = "\n\n".join(f"Фрагмент {i+1}:\n{c}" for i, c in enumerate(vector_context))
        system_content += f"\n\n📄 Контекст из загруженных документов:\n{context_text}"
    else:
        # Можно добавить уведомление, что контекст не найден (опционально)
        pass

    # Собираем сообщения для API
    messages = [{"role": "system", "content": system_content}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    try:
        logger.info(f"User {user_id} request: {user_text}")

        # Вызываем API в отдельном потоке, чтобы не блокировать event loop
        response_data = await asyncio.to_thread(
            api_client.generate_response,
            messages=messages,
            temperature=config.DEFAULT_TEMPERATURE,
            max_tokens=config.DEFAULT_MAX_TOKENS,
            model=config.DEFAULT_MODEL
        )

        reply = response_data['content']
        usage = response_data.get('usage', {})
        logger.info(f"Response tokens: {usage}")

        # Сохраняем диалог в короткую память
        context_manager.add_message(user_id, "user", user_text)
        context_manager.add_message(user_id, "assistant", reply)

        await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Error processing user {user_id}: {e}")
        await update.message.reply_text("❌ Извините, произошла ошибка при обработке запроса. Попробуйте позже.")


def main() -> None:
    """Запуск бота."""
    builder = Application.builder().token(config.BOT_TOKEN)
    if config.TELEGRAM_API_BASE_URL:
        builder = builder.base_url(config.TELEGRAM_API_BASE_URL)
        logger.info(f"Используется базовый URL: {config.TELEGRAM_API_BASE_URL}")

    builder = builder.connect_timeout(60.0).read_timeout(120.0)
    application = builder.build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(CommandHandler("cleardocs", cleardocs))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запущен с поддержкой короткой и долгой памяти")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()