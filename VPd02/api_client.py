"""
Модуль для работы с Exchange Rate API.
Содержит функцию получения курсов валют для заданной базовой валюты.
"""

import requests
from typing import Dict, Optional

# Константа базового URL API (открытый доступ без ключа)
API_BASE_URL = "https://open.er-api.com/v6/latest"


def get_currency_rates(base: str) -> Optional[Dict]:
    """
    Получает актуальные курсы валют для указанной базовой валюты.

    Args:
        base (str): Трёхбуквенный код базовой валюты (например, 'USD').

    Returns:
        Optional[Dict]: Словарь с данными ответа API (как в документации)
                        или None в случае ошибки.
    """
    url = f"{API_BASE_URL}/{base.upper()}"
    try:
        response = requests.get(url, timeout=10)
    except requests.RequestException as e:
        print(f"[Ошибка сети] Не удалось соединиться с API: {e}")
        return None

    if response.status_code != 200:
        print(f"[Ошибка HTTP] Статус {response.status_code} для {base}")
        return None

    data = response.json()
    # Проверяем, что API вернул успешный результат
    if data.get("result") != "success":
        print(f"[Ошибка API] Неожиданный ответ: {data.get('result')}")
        return None

    return data