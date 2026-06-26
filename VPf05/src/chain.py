#!/usr/bin/env python3
"""
Цепочка для генерации статьи с использованием LangChain и OpenAIClient.
Соблюдает принципы SOLID: каждый этап вынесен в отдельную функцию,
зависимость от LLM абстрагирована через Runnable интерфейс.
"""

import os
import sys
import json
import re
import argparse
import logging
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

# Импорты из нашего пакета
from .openai_client import OpenAIClient
from .config import Config

# Загружаем переменные окружения (уже делает Config, но для уверенности)
load_dotenv()

# -------------------- Настройка логирования --------------------
def setup_logger() -> None:
    level_name = Config.LOG_LEVEL
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

logger = logging.getLogger(__name__)

# -------------------- Адаптер для OpenAI (через Runnable) --------------------
def _lc_to_openai_messages(messages: List[BaseMessage]) -> List[Dict[str, str]]:
    """Преобразует сообщения LangChain в формат OpenAI API."""
    role_map = {
        SystemMessage: "system",
        HumanMessage: "user",
        AIMessage: "assistant",
    }
    converted = []
    for m in messages:
        role = None
        for cls, r in role_map.items():
            if isinstance(m, cls):
                role = r
                break
        if role is None:
            role = "user"
        content = m.content if isinstance(m.content, str) else str(m.content)
        converted.append({"role": role, "content": content})
    return converted


def get_llm() -> Runnable:
    """
    Возвращает Runnable, который использует OpenAIClient для вызова модели.
    Настройки (api_key, model, base_url) берутся из Config.
    """
    Config.validate()  # проверяем наличие ключа
    api_key = Config.OPENAI_API_KEY
    model = Config.OPENAI_MODEL
    base_url = Config.OPENAI_BASE_URL

    if not base_url:
        logger.warning("⚠️  Переменная OPENAI_BASE_URL не задана! Будет использован стандартный URL OpenAI.")
        logger.warning("⚠️  Если вы используете прокси, укажите OPENAI_BASE_URL в .env")
    else:
        logger.info(f"✅ OPENAI_BASE_URL прочитан: {base_url}")

    client = OpenAIClient(api_key, model, base_url=base_url)
    temperature = Config.TEMPERATURE

    logger.debug("Инициализация LLM через OpenAIClient: model=%s, base_url=%s, temperature=%.1f",
                 model, base_url, temperature)

    def _invoke(messages_or_value: Any) -> str:
        if hasattr(messages_or_value, "to_messages"):
            lc_messages = messages_or_value.to_messages()
        else:
            lc_messages = messages_or_value
        if not isinstance(lc_messages, list):
            raise TypeError("Ожидается список сообщений для LLM")
        oa_messages = _lc_to_openai_messages(lc_messages)
        return client.generate_response(oa_messages, temperature=temperature)

    return RunnableLambda(_invoke)


# -------------------- Утилиты --------------------
def strip_code_fences(text: str) -> str:
    """Удаляет обратные кавычки, если модель вернула код с маркдауном."""
    pattern = r"^\s*```[a-zA-Z]*\s*\n|\n\s*```\s*$"
    return re.sub(pattern, "", text, flags=re.MULTILINE)


def parse_json_spec(text: str) -> Dict[str, Any]:
    """Пытается распарсить JSON из текста (с запасным извлечением)."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))
        raise ValueError("Не удалось извлечь JSON из ответа модели.")


def slugify(text: str) -> str:
    """Преобразует текст в безопасное имя файла."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "article"


# -------------------- Построение цепочек (каждый этап — отдельная функция) --------------------
def build_analysis_chain(llm: Runnable) -> Runnable:
    """
    Этап 1: Анализ темы.
    Возвращает JSON с ключами: topic, audience, style, key_points.
    """
    system = (
        "Ты — опытный аналитик контента. Проанализируй тему статьи и выдели:\n"
        "- основную тему (topic),\n"
        "- целевую аудиторию (audience),\n"
        "- рекомендуемый стиль (style): научный, публицистический, обучающий, развлекательный,\n"
        "- ключевые аспекты, которые обязательно нужно осветить (key_points) — список из 3-5 пунктов.\n"
        "Ответ должен быть строго в формате JSON, без пояснений."
    )
    human = "Тема статьи: {topic}"
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", human),
    ])
    return prompt | llm | StrOutputParser()


def build_source_chain(llm: Runnable) -> Runnable:
    """
    Этап 2: Подбор инструментов / источников.
    Возвращает JSON с ключами: data_sources (список источников), tools (список инструментов, например, API).
    """
    system = (
        "Ты — архитектор данных. Для заданной темы и анализа предложи:\n"
        "- data_sources: какие внешние источники информации могут быть полезны (например, Википедия, научные статьи, новостные сайты),\n"
        "- tools: какие инструменты или API можно использовать (например, поисковик, база знаний, переводчик).\n"
        "Ответ в формате JSON."
    )
    human = (
        "Анализ темы:\n{analysis_json}\n\n"
        "Предложи источники и инструменты."
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", human),
    ])
    return prompt | llm | StrOutputParser()


def build_plan_chain(llm: Runnable) -> Runnable:
    """
    Этап 3: Генерация плана статьи.
    Возвращает JSON со структурой: разделы (sections) — список заголовков и подзаголовков.
    """
    system = (
        "Ты — редактор. На основе темы и анализа создай детальный план статьи в формате JSON.\n"
        "Структура: {{ \"sections\": [{{ \"title\": \"Заголовок\", \"subsections\": [\"Подзаголовок1\", ...] }}, ...] }}\n"
        "План должен быть логичным, охватывать все ключевые аспекты."
    )
    human = (
        "Тема: {topic}\n"
        "Анализ: {analysis_json}\n"
        "Источники/инструменты: {sources_json}\n\n"
        "Создай план статьи."
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", human),
    ])
    return prompt | llm | StrOutputParser()


def build_writing_chain(llm: Runnable) -> Runnable:
    """
    Этап 4: Написание полного текста статьи на основе плана.
    Возвращает Markdown-текст.
    """
    system = (
        "Ты — профессиональный писатель. Напиши полноценную статью в формате Markdown на основе плана.\n"
        "Статья должна быть содержательной, структурированной, с введением, основной частью и заключением.\n"
        "Используй заголовки (#, ##, ###) согласно плану. Стиль должен соответствовать анализу.\n"
        "Не добавляй лишних пояснений, только текст статьи."
    )
    human = (
        "Тема: {topic}\n"
        "Анализ: {analysis_json}\n"
        "План: {plan_json}\n\n"
        "Напиши статью."
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", human),
    ])
    return prompt | llm | StrOutputParser()


def build_review_chain(llm: Runnable) -> Runnable:
    """
    Этап 5 (опциональный): Ревью и доработка текста.
    Возвращает исправленный текст (Markdown).
    """
    system = (
        "Ты — опытный редактор. Проверь статью на:\n"
        "- грамматические и стилистические ошибки,\n"
        "- логическую связность,\n"
        "- соответствие теме и стилю.\n"
        "Исправь все недочёты и верни исправленный полный текст в Markdown.\n"
        "Если ошибок нет, просто верни оригинал."
    )
    human = (
        "Оригинальная статья:\n{article}\n\n"
        "Исправь, если необходимо."
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", human),
    ])
    return prompt | llm | StrOutputParser()


# -------------------- Основная цепочка (оркестрация) --------------------
def run_chain(topic: str, out_dir: Path) -> Path:
    """
    Выполняет все этапы цепочки последовательно и сохраняет финальную статью.
    """
    llm = get_llm()

    # 1. Анализ темы
    logger.info("Шаг 1: Анализ темы...")
    analysis_chain = build_analysis_chain(llm)
    analysis_text = analysis_chain.invoke({"topic": topic})
    try:
        analysis = parse_json_spec(analysis_text)
    except Exception as e:
        logger.error("Не удалось распарсить анализ: %s", e)
        # Повторный запрос с жёстким требованием JSON
        enforce_prompt = ChatPromptTemplate.from_messages([
            ("system", "Верни только корректный JSON."),
            ("human", "Тема: {topic}"),
        ])
        analysis_text = (enforce_prompt | llm | StrOutputParser()).invoke({"topic": topic})
        analysis = parse_json_spec(analysis_text)
    analysis_json = json.dumps(analysis, ensure_ascii=False, indent=2)
    logger.debug("Анализ:\n%s", analysis_json)

    # 2. Подбор источников
    logger.info("Шаг 2: Подбор источников и инструментов...")
    source_chain = build_source_chain(llm)
    sources_text = source_chain.invoke({"analysis_json": analysis_json})
    try:
        sources = parse_json_spec(sources_text)
    except Exception as e:
        logger.error("Не удалось распарсить источники: %s", e)
        sources = {"data_sources": [], "tools": []}
    sources_json = json.dumps(sources, ensure_ascii=False, indent=2)
    logger.debug("Источники:\n%s", sources_json)

    # 3. Генерация плана
    logger.info("Шаг 3: Генерация плана статьи...")
    plan_chain = build_plan_chain(llm)
    plan_text = plan_chain.invoke({
        "topic": topic,
        "analysis_json": analysis_json,
        "sources_json": sources_json,
    })
    try:
        plan = parse_json_spec(plan_text)
    except Exception as e:
        logger.error("Не удалось распарсить план: %s", e)
        plan = {"sections": [{"title": "Введение", "subsections": []}]}
    plan_json = json.dumps(plan, ensure_ascii=False, indent=2)
    logger.debug("План:\n%s", plan_json)

    # 4. Написание статьи
    logger.info("Шаг 4: Написание статьи...")
    writing_chain = build_writing_chain(llm)
    article = writing_chain.invoke({
        "topic": topic,
        "analysis_json": analysis_json,
        "plan_json": plan_json,
    })
    article = strip_code_fences(article).strip()
    logger.debug("Статья (первые 300 символов):\n%s", article[:300])

    # 5. Ревью (дополнительный шаг для повышения качества)
    logger.info("Шаг 5: Ревью и финальная корректировка...")
    review_chain = build_review_chain(llm)
    reviewed = review_chain.invoke({"article": article})
    reviewed = strip_code_fences(reviewed).strip()
    final_article = reviewed if len(reviewed) > len(article) * 0.5 else article

    # Сохранение файла
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"article_{slugify(topic)[:50]}.md"
    out_path = out_dir / filename
    out_path.write_text(final_article, encoding="utf-8")
    logger.info("Статья сохранена в %s", out_path.resolve())

    return out_path


# -------------------- Точка входа (для самостоятельного запуска) --------------------
def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Генерация статьи через цепочку запросов.")
    parser.add_argument(
        "topic",
        type=str,
        help="Тема статьи (на любом языке)."
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="./output",
        help="Папка для сохранения статьи (по умолчанию ./output)."
    )
    args = parser.parse_args(argv)

    setup_logger()

    try:
        out_file = run_chain(args.topic, Path(args.out_dir))
    except Exception as e:
        logger.error("Ошибка выполнения: %s", e, exc_info=True)
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1

    print(f"Готово: {out_file.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())