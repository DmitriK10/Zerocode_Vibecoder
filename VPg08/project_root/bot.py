import logging
import os
import signal
import sys
import uuid
from datetime import datetime
from typing import Dict

import telebot
from haystack.dataclasses import Document
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import Config
from pipelines import (
    DocumentStoreFactory,
    IndexingPipeline,
    QueryPipeline,
    SummarizationPipeline,
)

# Настройка логирования
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "bot.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BotHandler:
    """
    Основной обработчик команд и сообщений телеграм-бота.
    Управляет сессиями прослушивания, индексацией и поиском.
    """

    def __init__(self, bot, indexing_pipeline, query_pipeline, summarization_pipeline):
        """
        Инициализирует обработчик с переданными зависимостями.

        :param bot: экземпляр TeleBot.
        :param indexing_pipeline: пайплайн индексации.
        :param query_pipeline: пайплайн поиска.
        :param summarization_pipeline: пайплайн суммаризации.
        """
        self.bot = bot
        self.indexing_pipeline = indexing_pipeline
        self.query_pipeline = query_pipeline
        self.summarization_pipeline = summarization_pipeline
        self.sessions: Dict[int, str] = {}
        self.bot_username = None
        self._register_handlers()

    def _register_handlers(self):
        """Регистрирует обработчики команд и сообщений в Telegram."""
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            self._send_welcome(message)

        @self.bot.message_handler(commands=['start_listening'])
        def start_listening(message):
            self._start_listening(message)

        @self.bot.message_handler(commands=['stop_listening'])
        def stop_listening(message):
            self._stop_listening(message)

        @self.bot.message_handler(func=lambda message: True)
        def handle_message(message):
            self._handle_message(message)

    def _send_welcome(self, message):
        """Отправляет приветственное сообщение с описанием команд."""
        self.bot.reply_to(
            message,
            "👋 Я бот-помощник для командных обсуждений.\n\n"
            "Команды:\n"
            "/start_listening – начать запись сессии (все сообщения сохраняются)\n"
            "/stop_listening – завершить сессию и получить резюме диалога\n"
            "Просто упомяни меня с вопросом – я поищу ответ в истории чата."
        )

    def _start_listening(self, message):
        """
        Начинает сессию прослушивания для данного чата.
        Сохраняет session_id в словаре активных сессий.
        """
        chat_id = message.chat.id
        if chat_id in self.sessions:
            self.bot.reply_to(message, "⚠️ Уже идет запись сессии. Используй /stop_listening для завершения.")
            return
        session_id = str(uuid.uuid4())
        self.sessions[chat_id] = session_id
        self.bot.reply_to(message, f"🔴 Начинаю запись сессии `{session_id[:8]}`. Все сообщения будут сохранены. Для завершения используй /stop_listening.")

    def _stop_listening(self, message):
        """
        Завершает сессию прослушивания, собирает все сообщения сессии
        и генерирует резюме диалога.
        """
        chat_id = message.chat.id
        session_id = self.sessions.pop(chat_id, None)
        if not session_id:
            self.bot.reply_to(message, "⚠️ Нет активной сессии. Используй /start_listening.")
            return

        self.bot.reply_to(message, "⏳ Завершаю сессию и формирую резюме...")

        # Используем структурированный фильтр для поиска по session_id
        filters = {
            "field": "session_id",
            "operator": "==",
            "value": session_id
        }
        try:
            docs = self.indexing_pipeline.document_store.filter_documents(filters=filters)
            logger.info(f"Total documents in Pinecone: {len(docs)}")
            # Сортировка не гарантируется, поэтому сортируем по timestamp
            docs.sort(key=lambda d: d.meta.get("timestamp", ""))
            logger.info(f"Found {len(docs)} documents for session {session_id[:8]}")
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            self.bot.reply_to(message, "❌ Ошибка при получении сообщений сессии. Проверьте логи.")
            return

        if not docs:
            self.bot.reply_to(message, "📭 За период сессии не было сохранено сообщений.")
            return

        try:
            summary = self.summarization_pipeline.run(docs)
            self.bot.reply_to(message, f"📝 **Резюме диалога:**\n\n{summary}")
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            self.bot.reply_to(message, "❌ Не удалось сгенерировать резюме. Проверьте логи.")

    def _handle_message(self, message):
        """
        Обрабатывает каждое входящее сообщение:
        - индексирует его с метаданными;
        - если это упоминание бота, выполняет поиск по истории чата.
        """
        chat_id = message.chat.id
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        text = message.text or ""

        # Определяем имя бота (кэшируем после первого запроса)
        if self.bot_username is None:
            try:
                self.bot_username = self.bot.get_me().username
                logger.info(f"Bot username set to: @{self.bot_username}")
            except Exception as e:
                logger.error(f"Failed to get bot username: {e}")
                return

        mention_candidates = [f"@{self.bot_username}"]
        if self.bot_username.endswith("_bot"):
            mention_candidates.append(f"@{self.bot_username[:-4]}")

        is_mention = any(cand in text for cand in mention_candidates)

        # 1. Индексация сообщения с флагом is_mention
        session_id = self.sessions.get(chat_id)
        meta = {
            "chat_id": chat_id,
            "user_id": user_id,
            "username": username,
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id if session_id else "",
            "is_mention": is_mention,
        }
        doc = Document(content=text, meta=meta)
        try:
            self.indexing_pipeline.run([doc])
            logger.info(f"Indexed message from {username} (chat {chat_id}): {text[:50]}...")
        except Exception as e:
            logger.error(f"Indexing error: {e}")

        # 2. Если это упоминание – выполняем поиск
        if is_mention:
            logger.info("Mention detected!")
            query = text
            for cand in mention_candidates:
                if cand in query:
                    query = query.replace(cand, "").strip()
                    break

            if not query:
                self.bot.reply_to(message, "🤔 Напиши вопрос после упоминания.")
                return

            filters = {
                "field": "chat_id",
                "operator": "==",
                "value": chat_id
            }
            try:
                docs = self.query_pipeline.run(query, filters=filters)
            except Exception as e:
                logger.error(f"Search error: {e}")
                self.bot.reply_to(message, "❌ Ошибка поиска. Проверьте логи.")
                return

            # Постфильтрация по тексту (исключаем упоминания)
            filtered_docs = [
                d for d in docs
                if not any(cand in d.content for cand in mention_candidates)
            ]

            if not filtered_docs:
                self.bot.reply_to(message, "🔍 Не нашёл релевантных сообщений по твоему вопросу.")
                return

            response_lines = ["Вот что я нашёл по твоему вопросу:"]
            for i, doc in enumerate(filtered_docs[:3], 1):
                author = doc.meta.get("username", "неизвестный")
                content = doc.content
                response_lines.append(f"{i}. @{author}: {content}")
            self.bot.reply_to(message, "\n".join(response_lines))


def shutdown_handler(signum, frame):
    """
    Обработчик сигналов для корректного завершения бота.
    """
    logger.info("Received signal to terminate. Stopping bot...")
    # В текущей реализации telebot не предоставляет явного stop_polling,
    # но мы можем выйти из программы.
    sys.exit(0)


if __name__ == "__main__":
    # Настройка graceful shutdown
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    config = Config()
    config.validate()

    bot = telebot.TeleBot(config.TELEGRAM_BOT_TOKEN)

    document_store = DocumentStoreFactory.create(config)
    indexing_pipeline = IndexingPipeline(document_store, config)
    query_pipeline = QueryPipeline(document_store, config)
    summarization_pipeline = SummarizationPipeline(config)

    handler = BotHandler(bot, indexing_pipeline, query_pipeline, summarization_pipeline)

    logger.info("Starting bot...")
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
    finally:
        logger.info("Bot has been stopped.")