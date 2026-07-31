# /home/user/animal_facts_agent/main.py
import os
import json
import re
import logging
import sqlite3
from typing import List
from dataclasses import dataclass

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage

# ---------- Настройка логирования ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------- 1. Загрузка переменных окружения (SRP) ----------
def load_environment() -> None:
    """Загружает переменные из .env файла."""
    load_dotenv()
    logger.info("Переменные окружения загружены")

# ---------- 2. Определение структуры ответа (SRP) ----------
@dataclass
class FactResponse:
    """Структурированный ответ агента: список фактов."""
    facts: List[str]

# ---------- 3. Инструменты (SRP) ----------
@tool
def get_cat_fact(breed: str) -> str:
    """
    Возвращает факт о породе кошек.
    Это инструмент, который агент может вызывать.
    """
    # Нормализация ввода
    breed = breed.strip().lower()
    facts = {
        "золотая шиншилла": "Золотая шиншилла — это окрас, а не порода. Характеризуется золотистым подшерстком и чёрными кончиками волос.",
        "сиамская": "Сиамские кошки очень голосисты и общительны, любят быть в центре внимания.",
        "персидская": "Персидские кошки имеют длинную шерсть и плоскую морду, они спокойны и ласковы.",
        "мейн-кун": "Мейн-куны — одни из самых крупных домашних кошек, их вес может достигать 12 кг."
    }
    return facts.get(breed, f"Факт о породе {breed} не найден. Попробуйте другую.")

@tool
def get_dog_fact(breed: str) -> str:
    """
    Возвращает факт о породе собак.
    Это наш собственный дополнительный инструмент.
    """
    breed = breed.strip().lower()
    facts = {
        "лабрадор": "Лабрадоры — отличные пловцы, у них перепончатые лапы и водоотталкивающая шерсть.",
        "немецкая овчарка": "Немецкие овчарки широко используются в полиции и армии благодаря уму и преданности.",
        "бульдог": "Бульдоги имеют характерную «раскачивающуюся» походку из-за коротких ног и широкой груди.",
        "такса": "Таксы были выведены для охоты на барсуков, их длинное тело и короткие лапы помогают проникать в норы."
    }
    return facts.get(breed, f"Факт о породе {breed} не найден.")

# ---------- 4. Создание модели (SRP, DIP) ----------
def create_model() -> ChatOpenAI:
    """
    Создаёт и возвращает модель ChatOpenAI с параметрами из окружения.
    Используется прокси proxyapi.ru.
    Модель ограничена gpt-3.5-turbo-16k.
    """
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-16k"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        temperature=0.7,
        max_tokens=1500
    )

# ---------- 5. Создание агента (SRP, DIP) ----------
def create_agent(model, tools, system_prompt, checkpointer):
    """
    Создаёт агента LangGraph с переданными зависимостями.
    Используется принцип инверсии зависимостей.
    """
    logger.info("Создание агента с системным промптом...")
    return create_react_agent(
        model=model,
        tools=tools,
        prompt=system_prompt,
        checkpointer=checkpointer
    )

# ---------- 6. Парсинг ответа (SRP) ----------
def parse_response(content: str) -> FactResponse:
    """
    Парсит ответ модели в структурированный объект FactResponse.
    Поддерживает JSON в маркдаун-блоках и обычный текст.
    """
    logger.debug("Парсинг ответа: %s", content[:100])
    # Пытаемся извлечь JSON из маркдаун-блока
    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Ищем обычный JSON-объект в тексте
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end > start:
            json_str = content[start:end]
        else:
            json_str = content

    try:
        data = json.loads(json_str)
        facts = data.get("facts", [])
        if not isinstance(facts, list):
            facts = [str(facts)]
        return FactResponse(facts=facts)
    except json.JSONDecodeError:
        # Если JSON не найден, разбиваем текст построчно
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        return FactResponse(facts=lines)

# ---------- 7. Запуск агента с заданным пользователем (SRP) ----------
def run_agent(agent, user_id: int, message: str) -> List[str]:
    """
    Выполняет запрос к агенту для конкретного пользователя.
    Возвращает список фактов.
    """
    config = {"configurable": {"thread_id": f"user_{user_id}"}}
    inputs = {"messages": [HumanMessage(content=message)]}
    try:
        logger.info("Запрос от user_id=%d: %s", user_id, message[:50])
        result = agent.invoke(inputs, config=config)
        last_message = result["messages"][-1]
        content = last_message.content
        parsed = parse_response(content)
        logger.info("Извлечено фактов: %d", len(parsed.facts))
        return parsed.facts
    except Exception as e:
        logger.error("Ошибка при выполнении агента: %s", e)
        return [f"⚠️ Ошибка: {str(e)}"]

# ---------- 8. Точка входа (главная функция) ----------
def main():
    load_environment()

    # Системный промпт (вынесен в переменную)
    SYSTEM_PROMPT = """
    Ты — умный помощник, специалист по животным.
    Ты отвечаешь на запросы пользователей, предоставляя факты о породах кошек и собак.
    Ты должен возвращать ответ в виде JSON-объекта с полем "facts", содержащим список строк.
    Пример: {"facts": ["Факт 1", "Факт 2"]}
    Не добавляй лишнего текста, только JSON.
    """

    # Создаём зависимости
    model = create_model()
    tools = [get_cat_fact, get_dog_fact]   # два инструмента

    # Используем SQLite для долгосрочной памяти
    # Создаём соединение и инициализируем таблицы
    conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
    memory = SqliteSaver(conn)
    logger.info("Используется долгосрочная память (SQLite)")

    agent = create_agent(model, tools, SYSTEM_PROMPT, memory)

    # Тестируем
    print("=== Запрос пользователя 1 ===")
    facts1 = run_agent(agent, 1, "Расскажи факты о сиамских кошках")
    print("Факты:", facts1)

    print("\n=== Запрос пользователя 2 ===")
    facts2 = run_agent(agent, 2, "Факты о лабрадорах и таксах")
    print("Факты:", facts2)

    print("\n=== Запрос пользователя 1 (продолжение диалога) ===")
    facts3 = run_agent(agent, 1, "А что насчёт мейн-кунов?")
    print("Факты:", facts3)

    # Закрываем соединение с БД (опционально)
    conn.close()

if __name__ == "__main__":
    main()