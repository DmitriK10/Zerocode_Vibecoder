import sys
import os
import logging
import ssl
import certifi
import requests
from dotenv import load_dotenv
import telebot
import telebot.apihelper
from openai import OpenAI

# ===== ПРИНУДИТЕЛЬНО УКАЗЫВАЕМ СЕРТИФИКАТЫ ДЛЯ ВСЕХ HTTPS-ЗАПРОСОВ =====
os.environ['SSL_CERT_FILE'] = certifi.where()

# ===== НАСТРОЙКА SSL ДЛЯ TELEGRAM =====
session = requests.Session()
session.verify = certifi.where()
telebot.apihelper._session = session

ssl_context = ssl.create_default_context(cafile=certifi.where())
telebot.apihelper.ssl_context = ssl_context

# Добавляем папку src в путь
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from embedding_service import EmbeddingService
from pinecone_service import PineconeService
from searcher import Searcher

# --- Логирование ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- .env ---
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# --- Сервисы ---
embedding_service = EmbeddingService()
pinecone_service = PineconeService()
pinecone_service.connect_to_index()
searcher = Searcher(embedding_service, pinecone_service)

# --- OpenAI ---
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)
chat_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-16k")

# --- Telegram ---
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
if not bot_token:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env")
bot = telebot.TeleBot(bot_token)

# --- Вспомогательные функции ---
def get_embedding(text: str):
    return embedding_service.get_embedding(text)

def get_relevant_memories(user_id: int, query_text: str, top_k: int = 10):
    query_vec = get_embedding(query_text)
    filter_dict = {"user_id": str(user_id)}
    return pinecone_service.query_vectors(query_vec, top_k=top_k, filter_dict=filter_dict)

def save_memory(user_id: int, text: str, category: str = "auto", importance: str = "medium"):
    vec = get_embedding(text)
    import time
    vector_id = f"mem_{user_id}_{int(time.time())}"
    metadata = {
        "text": text,
        "category": category,
        "user_id": str(user_id),
        "importance": importance,
        "source": "telegram"
    }
    pinecone_service.upsert_vectors([{
        "id": vector_id,
        "values": vec,
        "metadata": metadata
    }])
    logger.info(f"Сохранено воспоминание для user {user_id}: {text[:50]}...")

def generate_response(user_id: int, user_message: str) -> str:
    memories = get_relevant_memories(user_id, user_message, top_k=10)
    context = "Вот что я знаю по этой теме (из ранее сохранённых воспоминаний):\n"
    if memories:
        for i, mem in enumerate(memories, 1):
            text = mem.get('metadata', {}).get('text', '')
            score = mem.get('score', 0.0)
            context += f"{i}. {text} (релевантность: {score:.2f})\n"
    else:
        context += "Пока нет подходящих воспоминаний.\n"
    system_prompt = (
        "Ты — умный помощник. Отвечай на вопросы пользователя, "
        "используя предоставленный контекст (воспоминания). "
        "Если контекст неполный, дополни его своими знаниями. "
        "Будь дружелюбным и полезным."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Контекст:\n{context}\n\nВопрос пользователя: {user_message}"}
    ]
    try:
        response = openai_client.chat.completions.create(
            model=chat_model,
            messages=messages,
            max_completion_tokens=1500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Ошибка генерации ответа: {e}")
        return "Извините, произошла ошибка при генерации ответа."

def should_remember(text: str) -> bool:
    keywords = ["запомни", "важно", "мой", "моя", "моё", "я люблю", "я хочу", "запомни, что"]
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)

# --- Обработчики ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 
        "Привет! Я бот с векторной памятью.\n"
        "Я запоминаю важные факты, которые ты мне говоришь, и использую их в ответах.\n"
        "Команды:\n"
        "/save <текст> — сохранить указанный текст в память\n"
        "Просто пиши мне сообщения, и я буду отвечать с учётом предыдущих разговоров."
    )

@bot.message_handler(commands=['save'])
def save_command(message):
    text = message.text.replace('/save', '', 1).strip()
    if not text:
        bot.reply_to(message, "Напишите текст для сохранения после команды /save.")
        return
    user_id = message.from_user.id
    save_memory(user_id, text)
    bot.reply_to(message, f"✅ Запомнил: «{text[:100]}»")

@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    user_id = message.from_user.id
    user_text = message.text
    if not user_text:
        return
    if should_remember(user_text):
        save_memory(user_id, user_text)
        bot.reply_to(message, "🔖 Я запомнил этот факт.")
    reply = generate_response(user_id, user_text)
    bot.reply_to(message, reply)

if __name__ == "__main__":
    logger.info("Бот запущен...")
    try:
        bot.polling(non_stop=True, interval=0, timeout=60)
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")