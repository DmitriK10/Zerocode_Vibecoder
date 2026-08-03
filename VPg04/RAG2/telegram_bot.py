"""
Telegram-бот для RAG-агента.
Использует PyTelegramBotAPI.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import telebot
from main import (
    RAGAgent, EmbeddingProvider, VectorStoreManager,
    Retriever, Generator, URLProcessor,
    OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL,
    PINECONE_API_KEY, PINECONE_INDEX_NAME, PINECONE_ENVIRONMENT
)

# Загрузка .env из папки проекта
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_API")
if not TELEGRAM_TOKEN:
    raise EnvironmentError("TELEGRAM_BOT_API не задан в .env")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация RAG-агента (те же зависимости, что и в main.py)
embed_provider = EmbeddingProvider(OPENAI_API_KEY, OPENAI_BASE_URL)
vector_manager = VectorStoreManager(
    api_key=PINECONE_API_KEY,
    index_name=PINECONE_INDEX_NAME,
    environment=PINECONE_ENVIRONMENT,
    embedding_provider=embed_provider
)
retriever = Retriever(vector_manager, k=5)
generator = Generator(OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL)
url_processor = URLProcessor()
rag = RAGAgent(retriever, generator, url_processor, vector_manager)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --------------------------- Обработчики команд ---------------------------

@bot.message_handler(commands=['start', 'help'])
def send_help(message):
    help_text = """
    🤖 Я RAG-агент. Умею:
    /search <вопрос> – найти ответ в базе знаний
    /add_url <url> – добавить содержимое страницы в базу
    /catfact – получить случайный факт о котах
    /ask <вопрос> – задать вопрос напрямую агенту (с поиском)
    """
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['search'])
def handle_search(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Укажите вопрос после /search")
        return
    query = parts[1].strip()
    bot.reply_to(message, "🔍 Ищу в базе знаний...")
    try:
        answer = rag.query(query, use_rag=True)
        bot.reply_to(message, answer)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

@bot.message_handler(commands=['add_url'])
def handle_add_url(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Укажите URL после /add_url")
        return
    url = parts[1].strip()
    bot.reply_to(message, f"📥 Загружаю и индексирую {url}...")
    try:
        result = rag.add_url_to_knowledge(url)
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

@bot.message_handler(commands=['catfact'])
def handle_catfact(message):
    bot.reply_to(message, "🐈 Запрашиваю факт...")
    try:
        result = rag.run_agent_with_tool("Дай случайный факт о котах")
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

@bot.message_handler(func=lambda msg: True)
def handle_any_message(message):
    query = message.text.strip()
    if not query:
        return
    bot.reply_to(message, "🤔 Думаю...")
    try:
        answer = rag.query(query, use_rag=True)
        bot.reply_to(message, answer)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

if __name__ == "__main__":
    logger.info("Бот запущен")
    bot.infinity_polling()