import httpx
import os
from haystack import component

@component
class DogImageComponent:
    @component.output_types(image_url=str)
    def run(self) -> dict:
        """
        Получает случайное изображение собаки с random.dog.
        Если возвращается не картинка, повторяет запрос до 5 раз.
        """
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        max_attempts = 5

        for attempt in range(max_attempts):
            try:
                response = httpx.get("https://random.dog/woof", timeout=10)
                response.raise_for_status()
                filename = response.text.strip()
                ext = os.path.splitext(filename)[1].lower()

                if ext in allowed_extensions:
                    image_url = f"https://random.dog/{filename}"
                    return {"image_url": image_url}
                # Если расширение не подходит, пробуем снова
            except Exception:
                continue

        return {"image_url": f"Ошибка: не удалось получить изображение после {max_attempts} попыток."}