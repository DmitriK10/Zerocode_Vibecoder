import httpx
from haystack import component

@component
class DogImageComponent:
    @component.output_types(image_url=str)
    def run(self) -> dict:
        """Получает случайное изображение собаки с random.dog"""
        try:
            response = httpx.get("https://random.dog/woof", timeout=10)
            response.raise_for_status()
            filename = response.text.strip()
            image_url = f"https://random.dog/{filename}"
            return {"image_url": image_url}
        except Exception as e:
            return {"image_url": f"Ошибка получения изображения: {str(e)}"}