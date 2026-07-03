import logging
import json
import re
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

from .config import Config
from .mcp_client import get_tools, call_tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Config.validate()

client = OpenAI(
    api_key=Config.OPENAI_API_KEY,
    base_url=Config.OPENAI_BASE_URL
)

# Получаем список инструментов с MCP-сервера (синхронно при старте)
import asyncio
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
mcp_tools = loop.run_until_complete(get_tools())
if isinstance(mcp_tools, dict) and "error" in mcp_tools:
    logger.error(f"Ошибка получения инструментов: {mcp_tools['error']}")
    mcp_tools = []

tools_description = "\n".join([
    f"- {t['name']}: {t['description']} (параметры: {', '.join(t.get('inputSchema', {}).get('properties', {}).keys())})"
    for t in mcp_tools
])

# Улучшенный системный промпт – теперь явно требуем только JSON
SYSTEM_PROMPT = f"""Ты — умный помощник для работы с кинотекой. Ты можешь использовать следующие инструменты:

{tools_description}

Когда пользователь просит что-то сделать, определи, какой инструмент нужен, и **верни только JSON** в формате:
{{"tool": "название_инструмента", "arguments": {{"параметр": "значение"}}}}

Если инструмент не нужен, просто ответь пользователю обычным текстом (без JSON).

Примеры для всех инструментов:
- "покажи все фильмы" → {{"tool": "list_movies", "arguments": {{}}}}
- "найди фильм Интерстеллар" → {{"tool": "find_movie_by_title", "arguments": {{"title": "Интерстеллар"}}}}
- "найди фильмы режиссёра Нолан" → {{"tool": "find_movies_by_director", "arguments": {{"director": "Нолан"}}}}
- "найди фильмы в жанре Фантастика" → {{"tool": "find_movies_by_genre", "arguments": {{"genre": "Фантастика"}}}}
- "добавь фильм Дюна режиссёр Дени Вильнёв жанр Фантастика год 2021 рейтинг 8.2" → {{"tool": "add_movie", "arguments": {{"title": "Дюна", "director": "Дени Вильнёв", "genre": "Фантастика", "year": 2021, "rating": 8.2}}}}
- "удали фильм с id 5" → {{"tool": "delete_movie", "arguments": {{"movie_id": 5}}}}
- "обнови рейтинг фильма 3 на 9.5" → {{"tool": "update_movie_rating", "arguments": {{"movie_id": 3, "new_rating": 9.5}}}}
- "покажи топ 3 фильма" → {{"tool": "get_top_movies", "arguments": {{"limit": 3}}}}
- "дай случайный фильм" → {{"tool": "get_random_movie", "arguments": {{}}}}

Дополнительные инструменты:
- "сколько будет 2+2" → {{"tool": "calculate", "arguments": {{"expression": "2+2"}}}}
- "погода в Москве" → {{"tool": "get_weather", "arguments": {{"city": "Москва"}}}}
- "курс доллара" → {{"tool": "get_exchange_rate", "arguments": {{"from_currency": "USD"}}}}
- "сгенерируй QR для текста Привет" → {{"tool": "generate_qr", "arguments": {{"data": "Привет"}}}}
- "поищи новости про ИИ" → {{"tool": "web_search", "arguments": {{"query": "новости про ИИ"}}}}

Отвечай на русском языке, будь дружелюбным и полезным.
"""

user_histories = {}

# ---------- Функция для извлечения JSON из текста ----------
def extract_json(text: str):
    """
    Находит в тексте подстроку, которая является валидным JSON-объектом,
    и возвращает его (как словарь) или None.
    """
    # Ищем первый символ '{'
    start = text.find('{')
    if start == -1:
        return None
    # Идём по строке и считаем баланс скобок
    balance = 0
    in_string = False
    escape = False
    for i, ch in enumerate(text[start:], start):
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
            continue
        if not in_string:
            if ch == '{':
                balance += 1
            elif ch == '}':
                balance -= 1
                if balance == 0:
                    # Нашли конец JSON
                    candidate = text[start:i+1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        # Если невалидный JSON, попробуем следующий
                        # Продолжаем поиск после этой позиции
                        return extract_json(text[i+1:])
    return None

# ---------- Обработчики ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 Привет! Я бот с доступом к MCP-серверу кинотеки.\n"
        "Я умею:\n"
        "🎬 Работать с фильмами (показать, найти по названию/режиссёру/жанру, добавить, удалить, обновить рейтинг, показать топ, случайный фильм)\n"
        "🧮 Вычислять выражения\n"
        "🌤 Показывать погоду\n"
        "💱 Показывать курс валют\n"
        "📱 Генерировать QR-коды\n"
        "🔍 Искать в интернете\n\n"
        "Просто напиши свой запрос, и я постараюсь помочь.\n"
        "Для очистки истории используй /reset."
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("🧹 История диалога очищена.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text

    history = user_histories.get(user_id, [])
    history.append({"role": "user", "content": user_text})

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + history[-10:]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )
        assistant_reply = response.choices[0].message.content.strip()
        logger.info(f"Assistant reply: {assistant_reply}")

        # Пытаемся извлечь JSON из ответа
        data = extract_json(assistant_reply)
        if data and isinstance(data, dict) and "tool" in data:
            tool_name = data["tool"]
            arguments = data.get("arguments", {})
            logger.info(f"Tool call: {tool_name} with {arguments}")
            result = await call_tool(tool_name, arguments)

            # Сохраняем в историю информацию о вызове и результат
            history.append({"role": "assistant", "content": f"Вызван инструмент {tool_name} с аргументами {arguments}"})
            history.append({"role": "assistant", "content": result})
            user_histories[user_id] = history

            # Отправляем результат (разбиваем при необходимости)
            if len(result) > 4096:
                for chunk in [result[i:i+4096] for i in range(0, len(result), 4096)]:
                    await update.message.reply_text(chunk)
            else:
                await update.message.reply_text(result)
            return

        # Если не JSON – отправляем как обычный текст
        history.append({"role": "assistant", "content": assistant_reply})
        user_histories[user_id] = history

        if len(assistant_reply) > 4096:
            for chunk in [assistant_reply[i:i+4096] for i in range(0, len(assistant_reply), 4096)]:
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(assistant_reply)

    except Exception as e:
        import traceback
        logger.error(f"Ошибка обработки сообщения от {user_id}: {e}\n{traceback.format_exc()}")
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

def main() -> None:
    builder = Application.builder().token(Config.BOT_TOKEN)
    if Config.TELEGRAM_API_BASE_URL:
        builder = builder.base_url(Config.TELEGRAM_API_BASE_URL)
        logger.info(f"Используется базовый URL: {Config.TELEGRAM_API_BASE_URL}")
    else:
        logger.info("Используется стандартный базовый URL")

    http_client = None
    if Config.PROXY_HOST and Config.PROXY_PORT:
        proxy_url = f"{Config.PROXY_TYPE}://{Config.PROXY_HOST}:{Config.PROXY_PORT}"
        logger.info(f"Используется прокси: {proxy_url}")
        http_client = httpx.AsyncClient(proxy=proxy_url, timeout=httpx.Timeout(60.0, connect=30.0))
        builder = builder.http_client(http_client)

    application = builder.build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запущен")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()