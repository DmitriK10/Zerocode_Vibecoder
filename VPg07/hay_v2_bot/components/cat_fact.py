import httpx
from haystack import component
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

@component
class CatFactComponent:
    @component.output_types(fact=str)
    def run(self, language: str = "ru") -> dict:
        """
        Получает случайный факт о кошках с catfact.ninja.
        Если language='ru', переводит на русский через OpenAI.
        """
        try:
            response = httpx.get("https://catfact.ninja/fact", timeout=10)
            response.raise_for_status()
            fact_en = response.json().get("fact", "No fact found.")

            if language == "ru":
                # Переводим на русский через OpenAI
                client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
                translation = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "Ты – переводчик. Переведи следующий текст с английского на русский язык. Ответь только переводом, без дополнительных пояснений."},
                        {"role": "user", "content": fact_en}
                    ],
                    max_tokens=100
                )
                fact_ru = translation.choices[0].message.content.strip()
                return {"fact": fact_ru}
            else:
                return {"fact": fact_en}

        except Exception as e:
            return {"fact": f"Ошибка получения факта: {str(e)}"}