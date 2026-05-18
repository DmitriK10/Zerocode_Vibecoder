"""
Модуль для получения и красивого вывода информации о стране.
Использует http_client для запроса к REST Countries API.
"""

from http_client import get
from colorama import Fore, Style, init

# Инициализируем colorama один раз при импорте
init(autoreset=True)

def display_country_info(country_name: str) -> None:
    """
    Запрашивает данные о стране и выводит их в консоль с цветовой разметкой.
    
    Args:
        country_name: название страны (на английском, например "Italy")
    """
    url = f"https://restcountries.com/v3.1/name/{country_name}"
    data = get(url)
    
    if not data:
        print(Fore.RED + f"Не удалось получить данные о стране '{country_name}'.")
        return
    
    # API возвращает список, берём первый элемент
    country = data[0]
    
    # Извлечение полей с проверкой наличия
    name_common = country.get("name", {}).get("common", "Н/Д")
    name_official = country.get("name", {}).get("official", "Н/Д")
    capital = ", ".join(country.get("capital", ["Н/Д"]))
    region = country.get("region", "Н/Д")
    subregion = country.get("subregion", "Н/Д")
    population = country.get("population", "Н/Д")
    area = country.get("area", "Н/Д")
    tld = ", ".join(country.get("tld", ["Н/Д"]))
    cca2 = country.get("cca2", "Н/Д")
    flag = country.get("flag", "Н/Д")
    maps_link = country.get("maps", {}).get("googleMaps", "Н/Д")
    
    # Языки
    langs = country.get("languages", {})
    languages = ", ".join(langs.values()) if langs else "Н/Д"
    
    # Валюты
    currencies = country.get("currencies", {})
    if currencies:
        curr_list = []
        for code, info in currencies.items():
            curr_list.append(f"{info.get('name', code)} ({info.get('symbol', '')})")
        currencies_str = ", ".join(curr_list)
    else:
        currencies_str = "Н/Д"
    
    # Вывод с цветами
    print(Fore.CYAN + Style.BRIGHT + f"\n=== Информация о стране: {name_common} ===")
    print(Fore.YELLOW + f"Официальное название: {name_official}")
    print(Fore.GREEN + f"Столица: {capital}")
    print(Fore.MAGENTA + f"Регион: {region} / {subregion}")
    print(Fore.BLUE + f"Население: {population:,}")
    print(Fore.BLUE + f"Площадь: {area:,} км²")
    print(Fore.WHITE + f"Языки: {languages}")
    print(Fore.WHITE + f"Валюты: {currencies_str}")
    print(Fore.CYAN + f"Домен верхнего уровня: {tld}")
    print(Fore.CYAN + f"Код страны (cca2): {cca2}")
    print(Fore.RED + f"Флаг: {flag}")
    print(Fore.LIGHTBLACK_EX + f"Карта Google: {maps_link}")
    print(Style.RESET_ALL)