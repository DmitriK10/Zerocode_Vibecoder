"""Кастомные исключения для обработки ошибок API и бота."""

class WeatherAPIError(Exception):
    """Базовое исключение для ошибок OpenWeatherMap."""
    pass

class GeocodingError(WeatherAPIError):
    """Ошибка при геокодинге (город не найден)."""
    pass

class ForecastError(WeatherAPIError):
    """Ошибка получения прогноза."""
    pass

class AirPollutionError(WeatherAPIError):
    """Ошибка получения данных о воздухе."""
    pass