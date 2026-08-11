import pytest
from unittest.mock import MagicMock, patch
from bot import BotHandler


class TestBotHandler:
    """Набор тестов для BotHandler."""

    def test_send_welcome(self, bot_handler, mock_telebot, sample_message):
        """Проверяет отправку приветственного сообщения."""
        message = sample_message()
        bot_handler._send_welcome(message)
        mock_telebot.reply_to.assert_called_once()

    def test_start_listening_already_running(self, bot_handler, mock_telebot, sample_message):
        """Проверяет, что повторный вызов start_listening выводит предупреждение."""
        message = sample_message(chat_id=123)
        bot_handler.sessions[123] = "existing"
        bot_handler._start_listening(message)
        mock_telebot.reply_to.assert_called_with(
            message,
            "⚠️ Уже идет запись сессии. Используй /stop_listening для завершения."
        )

    def test_start_listening_new(self, bot_handler, mock_telebot, sample_message):
        """Проверяет создание новой сессии."""
        message = sample_message(chat_id=123)
        bot_handler.sessions = {}
        with patch("uuid.uuid4", return_value="mocked-uuid"):
            bot_handler._start_listening(message)
        assert bot_handler.sessions[123] == "mocked-uuid"
        expected_msg = "🔴 Начинаю запись сессии `mocked-u`. Все сообщения будут сохранены. Для завершения используй /stop_listening."
        mock_telebot.reply_to.assert_called_with(message, expected_msg)

    def test_stop_listening_no_session(self, bot_handler, mock_telebot, sample_message):
        """Проверяет, что stop_listening без активной сессии выводит предупреждение."""
        message = sample_message(chat_id=123)
        bot_handler.sessions = {}
        bot_handler._stop_listening(message)
        mock_telebot.reply_to.assert_called_with(
            message,
            "⚠️ Нет активной сессии. Используй /start_listening."
        )

    def test_stop_listening_with_session_empty(self, bot_handler, mock_telebot, sample_message):
        """Проверяет завершение сессии, когда нет сохранённых сообщений."""
        message = sample_message(chat_id=123)
        bot_handler.sessions[123] = "session123"
        bot_handler.indexing_pipeline.document_store.filter_documents = MagicMock(return_value=[])
        bot_handler.summarization_pipeline.run = MagicMock()
        bot_handler._stop_listening(message)
        mock_telebot.reply_to.assert_any_call(
            message,
            "⏳ Завершаю сессию и формирую резюме..."
        )
        mock_telebot.reply_to.assert_any_call(
            message,
            "📭 За период сессии не было сохранено сообщений."
        )

    @patch("bot.Document")
    def test_handle_message_indexing_only(self, mock_document, bot_handler, sample_message):
        """Проверяет, что обычное сообщение (без упоминания) только индексируется."""
        message = sample_message(text="Обычное сообщение")
        bot_handler.bot_username = "test_bot"
        bot_handler.indexing_pipeline.run = MagicMock()
        bot_handler._handle_message(message)
        bot_handler.indexing_pipeline.run.assert_called_once()
        # query_pipeline не вызывается, так как это не упоминание
        bot_handler.query_pipeline.run.assert_not_called()

    def test_handle_message_mention_without_query(self, bot_handler, mock_telebot, sample_message):
        """Проверяет, что если после упоминания нет вопроса, бот просит уточнить."""
        message = sample_message(text="@test_bot")
        bot_handler.bot_username = "test_bot"
        bot_handler.indexing_pipeline.run = MagicMock()
        bot_handler._handle_message(message)
        mock_telebot.reply_to.assert_called_with(
            message,
            "🤔 Напиши вопрос после упоминания."
        )

    def test_handle_message_mention_with_query(self, bot_handler, mock_telebot, sample_message):
        """Проверяет, что при упоминании с вопросом выполняется поиск с правильным фильтром."""
        message = sample_message(text="@test_bot вопрос")
        bot_handler.bot_username = "test_bot"
        bot_handler.indexing_pipeline.run = MagicMock()
        bot_handler.query_pipeline.run = MagicMock(return_value=[])
        bot_handler._handle_message(message)
        bot_handler.indexing_pipeline.run.assert_called_once()
        expected_filters = {"field": "chat_id", "operator": "==", "value": 123}
        bot_handler.query_pipeline.run.assert_called_once_with("вопрос", filters=expected_filters)
        mock_telebot.reply_to.assert_called_with(
            message,
            "🔍 Не нашёл релевантных сообщений по твоему вопросу."
        )

    def test_handle_message_mention_filters_mentions(self, bot_handler, mock_telebot, sample_message):
        """
        Проверяет, что из результатов поиска исключаются сообщения,
        содержащие упоминание бота.
        """
        from haystack.dataclasses import Document
        message = sample_message(text="@test_bot вопрос")
        bot_handler.bot_username = "test_bot"
        bot_handler.indexing_pipeline.run = MagicMock()

        # Создаём документы: один с упоминанием, другой без
        doc_mention = Document(content="@test_bot что-то", meta={"username": "user1"})
        doc_good = Document(content="Полезный ответ", meta={"username": "user2"})
        bot_handler.query_pipeline.run = MagicMock(return_value=[doc_mention, doc_good])

        bot_handler._handle_message(message)

        # Проверяем, что reply_to был вызван с правильным сообщением (только doc_good)
        expected_response = "Вот что я нашёл по твоему вопросу:\n1. @user2: Полезный ответ"
        mock_telebot.reply_to.assert_called_with(message, expected_response)

    def test_handle_message_mention_search_error(self, bot_handler, mock_telebot, sample_message):
        """Проверяет обработку ошибки поиска."""
        message = sample_message(text="@test_bot вопрос")
        bot_handler.bot_username = "test_bot"
        bot_handler.indexing_pipeline.run = MagicMock()
        bot_handler.query_pipeline.run = MagicMock(side_effect=Exception("Search failed"))
        bot_handler._handle_message(message)
        mock_telebot.reply_to.assert_called_with(
            message,
            "❌ Ошибка поиска. Проверьте логи."
        )