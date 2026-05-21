"""Вспомогательные функции: форматирование дат, температура и т.д."""
from datetime import datetime
from typing import Dict, Any

def kelvin_to_celsius(kelvin: float) -> int:
    """Переводит Кельвины в градусы Цельсия."""
    return int(kelvin - 273.15)

def format_timestamp(dt: int, timezone_offset: int = 0) -> str:
    """
    Форматирует Unix timestamp в строку времени с учётом часового пояса.
    :param dt: Unix timestamp
    :param timezone_offset: смещение в секундах
    """
    dt_utc = datetime.utcfromtimestamp(dt)
    # Упрощённо: просто прибавляем смещение (для демонстрации)
    # В реальном проекте лучше использовать pytz или zoneinfo
    local_dt = datetime.fromtimestamp(dt + timezone_offset)
    return local_dt.strftime("%d.%m.%Y %H:%M")

def aqi_description(aqi: int) -> str:
    """Возвращает текстовое описание индекса качества воздуха (AQI)."""
    descriptions = {
        1: "Отличное",
        2: "Хорошее",
        3: "Умеренное",
        4: "Плохое",
        5: "Очень плохое"
    }
    return descriptions.get(aqi, "Неизвестно")