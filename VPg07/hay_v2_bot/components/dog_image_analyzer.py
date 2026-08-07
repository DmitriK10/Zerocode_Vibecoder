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
            prompt = (
                "Опиши породу собаки на этом изображении. "
                "Расскажи краткую историю происхождения породы."
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
            return {"analysis": analysis}
        except Exception as e:
            return {"analysis": f"Ошибка анализа: {str(e)}"}