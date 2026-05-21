"""5-дневный прогноз с шагом 3 часа (5 Day / 3 Hour Forecast)."""
import aiohttp
from typing import List, Dict, Any
from exceptions import ForecastError
from utils import kelvin_to_celsius, format_timestamp

class Forecast:
    URL = "https://api.openweathermap.org/data/2.5/forecast"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_forecast(self, lat: float, lon: float, cnt: int = 40) -> Dict[str, Any]:
        """
        Возвращает прогноз на 5 дней (cnt максимум 40 записей по 3 часа).
        """
        params = {
            "lat": lat,
            "lon": lon,
            "cnt": cnt,
            "appid": self.api_key
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.URL, params=params) as resp:
                if resp.status != 200:
                    raise ForecastError(f"Ошибка прогноза: HTTP {resp.status}")
                data = await resp.json()

        # Обрабатываем список forecast-объектов
        processed_list = []
        for item in data.get("list", []):
            dt = item["dt"]
            temp_c = kelvin_to_celsius(item["main"]["temp"])
            description = item["weather"][0]["description"]
            processed_list.append({
                "datetime": dt,
                "temp_c": temp_c,
                "description": description,
                "humidity": item["main"]["humidity"],
                "wind_speed": item["wind"]["speed"]
            })

        return {
            "city_name": None,  # будет установлено в клиенте
            "list": processed_list,
            "timezone_offset": data.get("city", {}).get("timezone", 0)
        }