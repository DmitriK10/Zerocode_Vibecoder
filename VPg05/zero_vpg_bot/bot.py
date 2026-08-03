"""
Telegram-бот с долговременной памятью на основе Pinecone.
Использует PineconeManager для хранения и поиска сообщений пользователя.
"""

import os
import time
import telebot
from dotenv import load_dotenv
from pinecone_manager import PineconeManager
from openai import OpenAI

# Загрузка переменных окружения
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан в .env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-16k")

# Инициализация бота и менеджера Pinecone
bot = telebot.TeleBot(TELEGRAM_TOKEN)
memory_manager = PineconeManager()

# Инициализация клиента OpenAI для генерации ответов
openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL or None,
)


def generate_response(user_message: str, context: str) -> str:
    """
    Генерация ответа через OpenAI с учётом контекста из памяти.
    """
    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Ты полезный ассистент. Отвечай кратко и по делу."},
                {"role": "user", "content": f"Контекст из памяти:\n{context}\n\nВопрос пользователя: {user_message}"},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Ошибка при генерации ответа: {e}")
        return "Извините, произошла ошибка при обработке запроса."


def get_user_full_name(message) -> str:
    """Безопасное получение имени пользователя с фоллбеками."""
    first = message.from_user.first_name or ""
    last = message.from_user.last_name or ""
    username = message.from_user.username or ""
    if first or last:
        return f"{first} {last}".strip()
    if username:
        return f"@{username}"
    return "Пользователь"


@bot.message_handler(content_types=['text'])
def handle_message(message):
    """Обработка входящих текстовых сообщений."""
    user_id = str(message.from_user.id)
    user_name = get_user_full_name(message)
    user_message = message.text

    # 1. Поиск релевантного контекста в памяти
    similar_memories = memory_manager.query_by_text(user_message, top_k=3)
    context_parts = []
    for item in similar_memories:
        if item["metadata"] and "text" in item["metadata"]:
            context_parts.append(item["metadata"]["text"])
    context = "\n".join(context_parts) if context_parts else "Нет сохранённых данных."

    # 2. Генерация ответа бота
    bot_response = generate_response(user_message, context)

    # 3. Сохранение сообщения пользователя в память (только оригинальный текст!)
    doc_id = f"user_{user_id}_{int(time.time())}"
    metadata = {
        "user_id": user_id,
        "user_name": user_name,
        "text": user_message,          # сохраняем только текст сообщения
        "timestamp": time.time(),
    }

    # Запись с проверкой дубликатов
    result = memory_manager.upsert_document(doc_id, user_message, metadata)
    print(f"[Память] Действие: {result['action']}, сходство: {result['similarity_score']}")

    # 4. Отправка ответа пользователю
    bot.reply_to(message, bot_response)


if __name__ == "__main__":
    print("Бот запущен...")
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("Бот остановлен.")