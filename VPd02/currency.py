#!/usr/bin/env python3
"""
Главный скрипт конвертера валют.
Реализует логику «кэш или свежие данные», вызывает API при необходимости,
предоставляет CLI для просмотра курсов и конвертации.
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в путь для импорта модулей
sys.path.insert(0, str(Path(__file__).resolve().parent))

import api_client
import storage
import cli

# Целевые валюты для вывода по умолчанию
DEFAULT_TARGETS = ["RUB", "EUR", "GBP"]


def get_currency_data(base_currency: str, force_update: bool = False) -> dict:
    """
    Получает данные о курсах валют.
    Сначала проверяет кэш (если он свежий и не запрошено принудительное обновление).
    Если кэш устарел или отсутствует, делает запрос к API и сохраняет результат.
    """
    cached_data = storage.read_from_file()

    if (
        not force_update
        and cached_data is not None
        and cached_data.get("base_code") == base_currency.upper()
        and storage.is_cache_fresh()
    ):
        print(f"[Кэш] Использую сохранённые данные от {cached_data.get('time_last_update_utc')}")
        return cached_data

    print(f"[API] Запрашиваю свежие курсы для {base_currency.upper()}...")
    fresh_data = api_client.get_currency_rates(base_currency)
    if fresh_data is None:
        if cached_data is not None:
            print("[Предупреждение] API недоступен. Использую устаревший кэш.")
            return cached_data
        else:
            print("[Критическая ошибка] Невозможно получить данные ни из API, ни из кэша.")
            sys.exit(1)

    storage.save_to_file(fresh_data)
    return fresh_data


def main():
    print("=== Конвертер валют (Exchange Rate API) ===\n")

    base = input("Введите базовую валюту (например, USD, EUR, RUB): ").strip().upper()
    if not base:
        print("Ошибка: базовая валюта не может быть пустой.")
        return

    data = get_currency_data(base)

    # Исправлено: поле в ответе API называется "rates", а не "conversion_rates"
    rates = data.get("rates", {})
    if not rates:
        print("Ошибка: в ответе API отсутствуют курсы валют (поле 'rates').")
        return

    available_codes = cli.get_available_currencies(data)

    if base not in available_codes:
        print(f"Ошибка: валюта '{base}' не найдена в списке поддерживаемых.")
        print(f"Доступные валюты: {', '.join(available_codes[:20])}... (всего {len(available_codes)})")
        return

    # Передаём словарь rates (курсы) в функцию отображения
    cli.display_rates(base, rates, DEFAULT_TARGETS)

    answer = input("\nХотите конвертировать сумму? (y/n): ").strip().lower()
    if answer == 'y':
        cli.run_converter(data, available_codes)

    print("\nРабота завершена.")


if __name__ == "__main__":
    main()