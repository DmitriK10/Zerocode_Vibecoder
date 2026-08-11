import pytest
from unittest.mock import MagicMock

from config import Config
from pipelines import IndexingPipeline, QueryPipeline, SummarizationPipeline


@pytest.fixture
def mock_config():
    """Фикстура с мок-конфигом, содержащим тестовые ключи."""
    cfg = MagicMock(spec=Config)
    cfg.TELEGRAM_BOT_TOKEN = "test_token"
    cfg.OPENAI_API_KEY = "test_openai_key"
    cfg.OPENAI_BASE_URL = "https://api.proxyapi.ru/openai/v1"
    cfg.OPENAI_MODEL = "gpt-3.5-turbo-16k"
    cfg.EMBEDDING_MODEL = "text-embedding-3-small"
    cfg.PINECONE_API_KEY = "test_pinecone_key"
    cfg.PINECONE_INDEX_NAME = "test_index"
    cfg.PINECONE_HOST = "test-host.pinecone.io"
    return cfg


@pytest.fixture
def mock_document_store():
    """Создаёт мок PineconeDocumentStore."""
    return MagicMock()


@pytest.fixture
def indexing_pipeline(mock_document_store, mock_config):
    return IndexingPipeline(mock_document_store, mock_config)


@pytest.fixture
def query_pipeline():
    """Мок для QueryPipeline, используемый в тестах бота."""
    return MagicMock(spec=QueryPipeline)


@pytest.fixture
def summarization_pipeline(mock_config):
    return SummarizationPipeline(mock_config)


@pytest.fixture
def mock_telebot():
    """Мок объекта TeleBot."""
    bot = MagicMock()
    bot.get_me.return_value = MagicMock(username="test_bot")
    return bot


@pytest.fixture
def bot_handler(mock_telebot, indexing_pipeline, query_pipeline, summarization_pipeline):
    from bot import BotHandler
    return BotHandler(mock_telebot, indexing_pipeline, query_pipeline, summarization_pipeline)


@pytest.fixture
def sample_message():
    """Создаёт объект сообщения Telegram с заданными параметрами."""
    def _create_message(chat_id=123, user_id=1, username="testuser", text="Hello"):
        msg = MagicMock()
        msg.chat.id = chat_id
        msg.from_user.id = user_id
        msg.from_user.username = username
        msg.text = text
        return msg
    return _create_message