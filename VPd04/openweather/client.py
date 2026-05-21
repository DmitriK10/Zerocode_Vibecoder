"""Фасад, объединяющий все эндпоинты OpenWeather."""
from .geocoding import Geocoding
from .current_weather import CurrentWeather
from .forecast import Forecast
from .air_pollution import AirPollution

class OpenWeatherClient:
    """
    Главный клиент для работы с OpenWeather API.
    Следуя Dependency Inversion, все зависимости передаются через конструктор.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.geocoding = Geocoding(api_key)
        self.current_weather = CurrentWeather(api_key)
        self.forecast = Forecast(api_key)
        self.air_pollution = AirPollution(api_key)

    async def get_weather_by_city(self, city_name: str) -> dict:
        """
        Получить текущую погоду по названию города.
        Сначала выполняет геокодинг, затем запрос погоды.
        """
        lat, lon = await self.geocoding.get_coordinates(city_name)
        weather = await self.current_weather.get_weather(lat, lon)
        weather["city_name"] = city_name
        return weather

    async def get_forecast_by_city(self, city_name: str) -> dict:
        """Получить 5-дневный прогноз по названию города."""
        lat, lon = await self.geocoding.get_coordinates(city_name)
        forecast = await self.forecast.get_forecast(lat, lon)
        forecast["city_name"] = city_name
        return forecast

    async def get_air_quality_by_city(self, city_name: str) -> dict:
        """Получить качество воздуха по названию города."""
        lat, lon = await self.geocoding.get_coordinates(city_name)
        return await self.air_pollution.get_air_quality(lat, lon)

    async def get_weather_by_coords(self, lat: float, lon: float) -> dict:
        """Текущая погода по координатам (без геокодинга)."""
        return await self.current_weather.get_weather(lat, lon)

    async def get_city_by_coords(self, lat: float, lon: float) -> str:
        """Обратный геокодинг: получить название города по координатам."""
        return await self.geocoding.reverse_geocode(lat, lon)