"""
Модуль для низкоуровневой работы с HTTP.
Соблюдает принцип единственной ответственности (SRP).
"""

import requests
from typing import Optional, Dict, Any

def get(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """
    Выполняет GET-запрос к указанному URL.
    
    Args:
        url: полный адрес запроса
        params: словарь с query-параметрами (опционально)
        timeout: таймаут в секундах
        
    Returns:
        декодированный JSON (dict) при успехе (status 200), иначе None
        
    Принципы SOLID:
        - SRP: функция делает только одно – отправляет GET и возвращает результат.
        - OCP: при необходимости добавить POST/PUT можно без изменения этой функции.
    """
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()          # выбросит исключение для 4xx/5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[HTTP ошибка] {e}")
        return None