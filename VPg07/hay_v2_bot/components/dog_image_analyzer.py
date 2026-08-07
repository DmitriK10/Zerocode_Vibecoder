import httpx
import base64
from haystack import component
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

@component
class DogImageAnalyzerComponent:
    @component.output_types(analysis=str)
    def run(self, image_url: str) -> dict:
        """Скачивает изображение, отправляет в OpenAI для описания породы и истории"""
        try:
            img_response = httpx.get(image_url, timeout=15)
            img_response.raise_for_status()
            img_data = base64.b64encode(img_response.content).decode("utf-8")
            client = OpenAI(
                api_key=OPENAI_API_KEY,
                base_url=OPENAI_BASE_URL
            )
            # Улучшенный промпт
            prompt = (
                "Посмотри на изображение. Если на нём есть собака, опиши её породу и кратко расскажи историю происхождения породы. "
                "Если на изображении нет собаки, просто скажи: «На этом изображении нет собаки». "
                "Не описывай людей, даже если они присутствуют на фото."
            )
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            analysis = response.choices[0].message.content

            # Проверяем, не содержит ли ответ отказ
            refusal_phrases = [
                "не могу помочь",
                "не могу идентифицировать",
                "не могу описать",
                "извините",
                "не могу ответить"
            ]
            if any(phrase in analysis.lower() for phrase in refusal_phrases):
                analysis = "🐶 На этом изображении, похоже, нет собаки, или я не смог её распознать. Но вот картинка!"
            return {"analysis": analysis}
        except Exception as e:
            return {"analysis": f"Ошибка анализа: {str(e)}"}