"""
Модуль для взаимодействия с API exchangerate.host.
Предоставляет методы получения курса и конвертации валют.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

class CurrencyAPI:
    """Класс для работы с API курсов валют (SRP: отвечает только за API-запросы)"""
    
    BASE_URL = "http://api.exchangerate.host"
    
    def __init__(self):
        self.api_key = os.getenv("CURRENCY_API_KEY")
        if not self.api_key:
            raise ValueError("CURRENCY_API_KEY не найден в переменных окружения")
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Получить текущий курс обмена из from_currency в to_currency.
        Возвращает float курс (например, 1 USD = 0.85 EUR -> 0.85).
        """
        url = f"{self.BASE_URL}/convert"
        params = {
            "access_key": self.api_key,
            "from": from_currency.upper(),
            "to": to_currency.upper(),
            "amount": 1
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not data.get("success"):
                raise Exception(f"API error: {data.get('error', {}).get('info', 'Unknown error')}")
            return float(data["result"])
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Ошибка соединения с API: {e}")
        except (KeyError, ValueError) as e:
            raise RuntimeError(f"Неверный ответ от API: {e}")
    
    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Конвертировать сумму из одной валюты в другую"""
        rate = self.get_exchange_rate(from_currency, to_currency)
        return round(amount * rate, 2)


# Словарь для определения валюты по названию страны (можно расширять)
COUNTRY_CURRENCY_MAP = {
    "россия": "RUB",
    "russia": "RUB",
    "сша": "USD",
    "usa": "USD",
    "европа": "EUR",
    "europe": "EUR",
    "великобритания": "GBP",
    "uk": "GBP",
    "китай": "CNY",
    "china": "CNY",
    "япония": "JPY",
    "japan": "JPY",
    "швейцария": "CHF",
    "switzerland": "CHF",
    "канада": "CAD",
    "canada": "CAD",
    "австралия": "AUD",
    "australia": "AUD"
}

def get_currency_by_country(country_name: str) -> str:
    """Вернуть код валюты по названию страны (регистронезависимо)"""
    return COUNTRY_CURRENCY_MAP.get(country_name.strip().lower(), None)