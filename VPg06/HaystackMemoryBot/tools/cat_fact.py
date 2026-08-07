import httpx
from haystack import component

@component
class CatFactComponent:
    @component.output_types(fact=str)
    def run(self) -> dict:
        """Получает случайный факт о кошках с catfact.ninja"""
        try:
            response = httpx.get("https://catfact.ninja/fact", timeout=10)
            response.raise_for_status()
            fact = response.json().get("fact", "No fact found.")
            return {"fact": fact}
        except Exception as e:
            return {"fact": f"Ошибка получения факта: {str(e)}"}