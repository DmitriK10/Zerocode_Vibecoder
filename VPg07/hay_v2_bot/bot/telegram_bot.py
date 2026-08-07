import os
import tempfile
import logging
import time
import telebot
from telebot.types import Message
from config import (
    TELEGRAM_TOKEN, PINECONE_NAMESPACE_DOCS, OPENAI_API_KEY, OPENAI_BASE_URL,
    EMBEDDING_MODEL, TOP_K_RESULTS, PINECONE_NAMESPACE_MESSAGES
)
from components.message_context import MessageContextManager
from components.cat_fact import CatFactComponent
from components.dog_image import DogImageComponent
from components.dog_image_analyzer import DogImageAnalyzerComponent
from components.weather import WeatherComponent
from components.docling_converter import DoclingConverterComponent
from components.pinecone_helpers import upsert_documents, query_pinecone
from components.embedder import get_embedder
from pipelines.generation import generate_response
from haystack.components.preprocessors import DocumentSplitter
from docling.exceptions import ConversionError
from openai import APIConnectionError, APITimeoutError, APIStatusError
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 20 * 1024 * 1024
MAX_RETRIES = 3
RETRY_DELAY = 2

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Инициализация менеджеров
message_context = MessageContextManager()

# Инструменты
cat_fact = CatFactComponent()
dog_image = DogImageComponent()
dog_analyzer = DogImageAnalyzerComponent()
weather = WeatherComponent()

# Используем общий эмбеддер
doc_embedder = get_embedder()

def index_document(file_path: str, chat_id: int) -> str:
    """Индексация документа с батчингом эмбеддингов и прогресс-сообщениями."""
    bot.send_message(chat_id, "⏳ Конвертирую документ... (может занять несколько минут)")

    # Конвертация
    converter = DoclingConverterComponent()
    conv_result = converter.run(file_path=file_path)
    doc = conv_result["documents"][0]
    full_text = doc.content

    bot.send_message(chat_id, "⏳ Разбиваю на чанки...")
    splitter = DocumentSplitter(split_by="word", split_length=200, split_overlap=20)
    chunks = splitter.run(documents=[doc])["documents"]

    bot.send_message(chat_id, f"⏳ Генерирую эмбеддинги для {len(chunks)} чанков...")

    # Батчинг эмбеддингов
    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    batch_size = 20
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        texts = [chunk.content for chunk in batch]
        try:
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts
            )
            for j, data in enumerate(response.data):
                batch[j].embedding = data.embedding
        except Exception as e:
            logger.error(f"Ошибка батча эмбеддингов: {e}, пробуем по одному")
            for chunk in batch:
                try:
                    embedding = doc_embedder.run(text=chunk.content)["embedding"]
                    chunk.embedding = embedding
                except Exception as inner_e:
                    logger.error(f"Не удалось получить эмбеддинг: {inner_e}")
                    continue
        bot.send_message(chat_id, f"⏳ Обработано {min(i+batch_size, len(chunks))}/{len(chunks)} чанков...")

    # Сохранение в Pinecone
    upsert_documents(chunks, namespace=PINECONE_NAMESPACE_DOCS)
    bot.send_message(chat_id, "✅ Индексация завершена.")
    return full_text

def search_documents(query: str) -> list[str]:
    query_embedding = doc_embedder.run(text=query)["embedding"]
    docs = query_pinecone(query_embedding, namespace=PINECONE_NAMESPACE_DOCS, top_k=TOP_K_RESULTS)
    return [doc.content for doc in docs]

def generate_summary(text: str) -> str:
    prompt = f"Кратко опиши содержание следующего документа в одном предложении:\n\n{text[:2000]}"
    return generate_response(prompt, [])

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message: Message):
    logger.info(f"Команда /start или /help от {message.from_user.id}")
    bot.reply_to(message, (
        "Привет! Я персональный помощник с ИИ.\n\n"
        "📌 Что я умею:\n"
        "✅ Отвечать на вопросы, используя историю диалога.\n"
        "✅ Анализировать загруженные PDF/DOCX и отвечать по их содержанию.\n"
        "✅ Факты о кошках (напиши «факт о кошках»).\n"
        "✅ Фото собак с описанием породы (напиши «покажи собаку»).\n"
        "✅ Погода в городе (напиши «погода в Москве»).\n\n"
        "📎 Команды:\n"
        "/clear – очистить историю диалога\n"
        "/help – показать это сообщение"
    ))

@bot.message_handler(commands=['clear'])
def clear_history(message: Message):
    user_id = message.from_user.id
    logger.info(f"Очистка истории для {user_id}")
    message_context.clear_user_messages(user_id)
    bot.reply_to(message, "История диалога очищена.")

@bot.message_handler(content_types=['document'])
def handle_document(message: Message):
    user_id = message.from_user.id
    file_name = message.document.file_name
    file_size = message.document.file_size

    if file_size > MAX_FILE_SIZE:
        size_mb = file_size // (1024 * 1024)
        bot.reply_to(message, f"❌ Файл «{file_name}» слишком большой ({size_mb} МБ). Макс. 20 МБ.")
        return

    bot.reply_to(message, f"📄 Файл получен. Начинаю анализ...")
    logger.info(f"Документ от {user_id}: {file_name} ({file_size} байт)")

    tmp_path = None
    try:
        file_info = bot.get_file(message.document.file_id)
        # Создаём временный файл в папке проекта (для избежания проблем с правами)
        project_temp = os.path.join(os.getcwd(), "temp_files")
        os.makedirs(project_temp, exist_ok=True)
        # Уникальное имя
        import uuid
        temp_filename = f"{uuid.uuid4().hex}_{file_name}"
        tmp_path = os.path.join(project_temp, temp_filename)
        with open(tmp_path, 'wb') as f:
            downloaded_file = bot.download_file(file_info.file_path)
            f.write(downloaded_file)
        logger.info(f"Временный файл сохранён: {tmp_path}")

        # Проверяем, что файл существует и доступен для чтения
        if not os.path.exists(tmp_path):
            raise FileNotFoundError(f"Файл {tmp_path} не создан")
        if not os.access(tmp_path, os.R_OK):
            raise PermissionError(f"Нет прав на чтение {tmp_path}")

        full_text = index_document(tmp_path, message.chat.id)

        bot.send_message(message.chat.id, "📝 Генерирую резюме...")
        summary = generate_summary(full_text)
        bot.send_message(message.chat.id, f"✅ Готово! Резюме:\n\n{summary}")

    except ConversionError as e:
        error_msg = str(e)
        if "InvalidCxxCompiler" in error_msg:
            bot.reply_to(message, (
                "❌ Ошибка: не найден компилятор C++.\n"
                "Установите Visual Studio Build Tools:\n"
                "https://visualstudio.microsoft.com/ru/downloads/#build-tools-for-visual-studio-2022"
            ))
        elif "std::bad_alloc" in error_msg:
            bot.reply_to(message, (
                "❌ Ошибка: нехватка памяти при обработке PDF.\n"
                "Это может быть связано со сложной структурой документа (много изображений, таблиц).\n"
                "Попробуйте конвертировать файл в текстовый формат (DOCX) или уменьшить размер."
            ))
        else:
            bot.reply_to(message, f"❌ Ошибка конвертации: {error_msg}")
        logger.exception("ConversionError")

    except (APIConnectionError, APITimeoutError) as e:
        logger.exception("Сетевая ошибка OpenAI")
        bot.reply_to(message, f"❌ Ошибка подключения к OpenAI. Проверьте интернет и .env (OPENAI_BASE_URL={OPENAI_BASE_URL})")

    except Exception as e:
        logger.exception("Непредвиденная ошибка")
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

    finally:
        # Удаляем временный файл в любом случае
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
                logger.info(f"Временный файл удалён: {tmp_path}")
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл {tmp_path}: {e}")

@bot.message_handler(func=lambda m: True)
def handle_text(message: Message):
    user_id = message.from_user.id
    text = message.text.lower()
    logger.info(f"Текст от {user_id}: {text[:50]}...")

    if "кошк" in text or "кот" in text:
        bot.reply_to(message, cat_fact.run()["fact"])
        return

    if "собак" in text or "пес" in text or "щен" in text:
        img_result = dog_image.run()
        if "Ошибка" in img_result["image_url"]:
            bot.reply_to(message, img_result["image_url"])
            return
        analysis = dog_analyzer.run(image_url=img_result["image_url"])["analysis"]
        bot.send_photo(message.chat.id, img_result["image_url"], caption=analysis)
        return

    if "погод" in text or "температур" in text:
        import re
        city_match = re.search(r'в\s+([А-Яа-яЁё\s\-]+)', text)
        city = city_match.group(1).strip() if city_match else "Москва"
        weather_report = weather.run(city=city)["weather_report"]
        bot.reply_to(message, weather_report)
        return

    # RAG
    try:
        message_context.save_user_message(user_id, text)
        msg_context = message_context.retrieve_context(user_id, text)
        doc_context = search_documents(text)
        combined = msg_context + doc_context
        answer = generate_response(text, combined)
        bot.reply_to(message, answer)
    except (APIConnectionError, APITimeoutError) as e:
        logger.exception("Сетевая ошибка")
        bot.reply_to(message, "❌ Ошибка подключения к OpenAI. Проверьте интернет.")
    except Exception as e:
        logger.exception("Ошибка RAG")
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    logger.info("Бот запущен")
    bot.infinity_polling()