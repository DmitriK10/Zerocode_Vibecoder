import os
from haystack.components.agents import Agent
from haystack.tools import ComponentTool
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage
from haystack.utils import Secret  # <-- импорт Secret

from tools import (
    CatFactComponent,
    DogImageComponent,
    DogImageAnalyzerComponent,
    WeatherComponent
)
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

class HaystackAgent:
    def __init__(self):
        # Инициализация генератора с прокси
        # Передаём api_key через Secret.from_token()
        self.chat_generator = OpenAIChatGenerator(
            model=OPENAI_MODEL,
            api_key=Secret.from_token(OPENAI_API_KEY),
            api_base_url=OPENAI_BASE_URL
        )

        # Создаём инструменты из компонентов
        cat_tool = ComponentTool(
            component=CatFactComponent(),
            name="cat_fact",
            description="Возвращает случайный факт о кошках. Используй, когда пользователь спрашивает о кошках."
        )
        dog_image_tool = ComponentTool(
            component=DogImageComponent(),
            name="dog_image",
            description="Возвращает URL случайного изображения собаки. Используй, когда пользователь просит показать собаку."
        )
        dog_analyzer_tool = ComponentTool(
            component=DogImageAnalyzerComponent(),
            name="dog_analyzer",
            description="Анализирует изображение собаки по URL и возвращает описание породы и историю. Используй вместе с dog_image."
        )
        weather_tool = ComponentTool(
            component=WeatherComponent(),
            name="weather",
            description="Получает текущую погоду для указанного города. Используй, когда пользователь спрашивает о погоде."
        )

        self.tools = [cat_tool, dog_image_tool, dog_analyzer_tool, weather_tool]

        # Системный промпт с описанием всех инструментов
        system_prompt = """
        Ты — умный персональный помощник. Твои задачи:
        - Отвечать на вопросы пользователя, используя контекст прошлых бесед.
        - При необходимости вызывать инструменты:
          * cat_fact – для фактов о кошках.
          * dog_image – для получения изображения собаки.
          * dog_analyzer – для анализа изображения собаки (порода, история).
          * weather – для погоды в городе.
        - Всегда сохранять дружелюбный тон.
        - Если пользователь просит изображение собаки, сначала используй dog_image, затем dog_analyzer и верни результат вместе с картинкой (пользователь получит и картинку, и описание).
        """

        self.agent = Agent(
            chat_generator=self.chat_generator,
            system_prompt=system_prompt,
            tools=self.tools
        )

    def run(self, user_message: str, context: list[str] = None) -> str:
        """Запуск агента с учётом контекста"""
        messages = []
        if context:
            for ctx in context:
                messages.append(ChatMessage.from_system(ctx))
        messages.append(ChatMessage.from_user(user_message))
        result = self.agent.run(messages=messages)
        return result["last_message"].text