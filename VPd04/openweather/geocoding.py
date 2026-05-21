"""Прямой и обратный геокодинг через OpenWeatherMap Geo API."""
import aiohttp
from typing import Tuple
from exceptions import GeocodingError

class Geocoding:
    """Класс для преобразования город -> координаты и обратно."""

    GEO_URL = "http://api.openweathermap.org/geo/1.0/direct"
    REVERSE_URL = "http://api.openweathermap.org/geo/1.0/reverse"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_coordinates(self, city_name: str, limit: int = 1) -> Tuple[float, float]:
        """
        Возвращает (широта, долгота) для заданного города.
        :raises GeocodingError: если город не найден.
        """
        params = {
            "q": city_name,
            "limit": limit,
            "appid": self.api_key
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.GEO_URL, params=params) as resp:
                if resp.status != 200:
                    raise GeocodingError(f"Ошибка геокодинга: HTTP {resp.status}")
                data = await resp.json()
                if not data:
                    raise GeocodingError(f"Город '{city_name}' не найден")
                first = data[0]
                return first["lat"], first["lon"]

    async def reverse_geocode(self, lat: float, lon: float) -> str:
        """Возвращает название населённого пункта по координатам."""
        params = {
            "lat": lat,
            "lon": lon,
            "limit": 1,
            "appid": self.api_key
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.REVERSE_URL, params=params) as resp:
                if resp.status != 200:
                    raise GeocodingError(f"Ошибка обратного геокодинга: HTTP {resp.status}")
                data = await resp.json()
                if not data:
                    raise GeocodingError("Не удалось определить город по координатам")
                return data[0].get("name", "Неизвестно")