import telebot
from telebot.types import Message
import logging
from config import TELEGRAM_TOKEN
from haystack_agent import HaystackAgent
from context_manager import ContextManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
agent = HaystackAgent()
context_mgr = ContextManager()

user_context = {}  # временное хранилище для контекста (можно и в Pinecone)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message: Message):
    bot.reply_to(message, (
        "Привет! Я персональный помощник на базе Haystack. "
        "Я запоминаю историю наших разговоров, могу дать факт о кошках, "
        "показать и описать собаку, а также сообщить погоду. "
        "Используй /clear, чтобы очистить историю."
    ))

@bot.message_handler(commands=['clear'])
def clear_history(message: Message):
    user_id = message.from_user.id
    # Очищаем временную историю (можно также удалить документы из Pinecone)
    user_context[user_id] = []
    bot.reply_to(message, "История диалога очищена.")

@bot.message_handler(func=lambda m: True)
def handle_message(message: Message):
    user_id = message.from_user.id
    user_text = message.text

    # 1. Сохраняем сообщение пользователя в Pinecone (только текст)
    context_mgr.save_user_message(user_id, user_text)

    # 2. Получаем релевантный контекст из Pinecone (прошлые сообщения)
    past_context = context_mgr.retrieve_context(user_id, user_text)

    # 3. Запускаем агента с контекстом
    response_text = agent.run(user_text, context=past_context)

    # 4. Если ответ содержит URL изображения, отправляем его как фото с caption
    #    (упрощённо: проверяем, не начинается ли ответ с "http")
    if response_text.startswith("http") and any(ext in response_text for ext in ['.jpg','.png','.jpeg']):
        # Отправляем фото
        bot.send_photo(message.chat.id, response_text, caption="Вот ваше изображение собаки.")
        # Дополнительно можно отправить анализ, если он уже в ответе?
        # В данном случае мы ожидаем, что агент вернёт сразу описание, а не URL.
        # Для простоты предположим, что агент возвращает описание.
    else:
        bot.reply_to(message, response_text)

    # Сохраняем ответ бота? По заданию сохраняем только пользовательские сообщения, поэтому пропускаем.

if __name__ == "__main__":
    logger.info("Бот запущен...")
    bot.infinity_polling()