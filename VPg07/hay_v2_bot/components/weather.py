import httpx
from haystack import component
from config import WEATHER_API_KEY

@component
class WeatherComponent:
    @component.output_types(weather_report=str)
    def run(self, city: str) -> dict:
        """Получает текущую погоду для указанного города"""
        if not WEATHER_API_KEY:
            return {"weather_report": "API ключ для погоды не настроен."}
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": WEATHER_API_KEY,
                "units": "metric",
                "lang": "ru"
            }
            response = httpx.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            report = f"Погода в {city}: {desc}, температура {temp}°C"
            return {"weather_report": report}
        except Exception as e:
            return {"weather_report": f"Не удалось получить погоду: {str(e)}"}