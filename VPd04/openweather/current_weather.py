"""Текущая погода по координатам (Current Weather API)."""
import aiohttp
from typing import Dict, Any
from exceptions import WeatherAPIError
from utils import kelvin_to_celsius

class CurrentWeather:
    """Запрос текущей погоды."""

    URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Возвращает словарь с основными погодными параметрами.
        """
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.URL, params=params) as resp:
                if resp.status != 200:
                    raise WeatherAPIError(f"Не удалось получить погоду: HTTP {resp.status}")
                data = await resp.json()

        # Извлекаем нужные поля
        weather_desc = data["weather"][0]["description"] if data.get("weather") else "нет данных"
        temp_k = data["main"]["temp"]
        feels_like_k = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        wind_speed = data["wind"]["speed"]
        sunrise = data["sys"]["sunrise"]
        sunset = data["sys"]["sunset"]
        timezone_offset = data.get("timezone", 0)

        return {
            "temperature_c": kelvin_to_celsius(temp_k),
            "feels_like_c": kelvin_to_celsius(feels_like_k),
            "description": weather_desc,
            "humidity": humidity,
            "pressure": pressure,
            "wind_speed": wind_speed,
            "sunrise": sunrise,
            "sunset": sunset,
            "timezone_offset": timezone_offset,
            "raw": data
        }