"""
Модуль пользовательского интерфейса: ввод данных, валидация валют,
конвертация суммы, вывод результатов.
"""

from typing import Dict


def get_available_currencies(data: Dict) -> list:
    """
    Извлекает список доступных кодов валют из ответа API.
    В ответе open.er-api.com курсы находятся в поле "rates".
    """
    rates = data.get("rates", {})
    return list(rates.keys())


def validate_currency(code: str, available: list) -> bool:
    """Проверяет, существует ли код валюты в доступном списке."""
    return code.upper() in available


def convert_amount(amount: float, from_rate: float, to_rate: float) -> float:
    """Конвертирует сумму из одной валюты в другую по заданным курсам."""
    result = amount / from_rate * to_rate
    return round(result, 4)


def display_rates(base: str, rates_dict: Dict, target_codes: list) -> None:
    """
    Выводит курсы для заданного списка валют относительно базовой.
    rates_dict – словарь курсов (поле "rates" из ответа API).
    """
    print(f"\n--- Курсы валют относительно {base.upper()} ---")
    for code in target_codes:
        rate = rates_dict.get(code.upper())
        if rate is not None:
            print(f"1 {base.upper()} = {rate} {code.upper()}")
        else:
            print(f"Курс для {code.upper()} не найден")


def run_converter(data: Dict, available_codes: list) -> None:
    """
    Интерактивный режим конвертации суммы.
    data – полный ответ API (содержит поле "rates").
    """
    print("\n--- Конвертер суммы ---")
    from_currency = input("Введите код исходной валюты: ").strip().upper()
    if not validate_currency(from_currency, available_codes):
        print(f"Ошибка: валюта '{from_currency}' не поддерживается.")
        return

    to_currency = input("Введите код целевой валюты: ").strip().upper()
    if not validate_currency(to_currency, available_codes):
        print(f"Ошибка: валюта '{to_currency}' не поддерживается.")
        return

    try:
        amount = float(input("Введите сумму: ").strip())
    except ValueError:
        print("Ошибка: сумма должна быть числом.")
        return

    rates = data.get("rates", {})
    from_rate = rates.get(from_currency)
    to_rate = rates.get(to_currency)

    if from_rate is None or to_rate is None:
        print("Ошибка: отсутствуют курсы для одной из валют.")
        return

    result = convert_amount(amount, from_rate, to_rate)
    print(f"\nРезультат: {amount} {from_currency} = {result} {to_currency}")