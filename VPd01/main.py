"""
Главный модуль проекта. Обеспечивает интерактивное CLI-меню на русском языке.
"""

import json
from http_client import get
from country_info import display_country_info
from colorama import init, Fore, Style

# Инициализируем colorama для автоматического сброса цвета после каждого print
init(autoreset=True)

def print_json_pretty(data: dict) -> None:
    """Выводит словарь в отформатированном JSON-виде."""
    print(Fore.CYAN + json.dumps(data, indent=2, ensure_ascii=False))

def get_random_dog() -> None:
    """Запрашивает случайную фотографию собаки и выводит ссылку."""
    url = "https://dog.ceo/api/breeds/image/random"
    data = get(url)
    if data and "message" in data:
        print(Fore.GREEN + f"Ссылка на случайную собаку:\n{data['message']}")
    else:
        print(Fore.RED + "Не удалось получить изображение собаки.")

def main():
    """Основное меню программы."""
    while True:
        print(Fore.YELLOW + Style.BRIGHT + "\n=== Выберите действие ===")
        print("1. Выполнить GET-запрос по URL")
        print("2. Информация о стране (REST Countries)")
        print("3. Случайная собака (dog.ceo)")
        print("0. Выход")
        
        choice = input(Fore.WHITE + "Ваш выбор: ").strip()
        
        if choice == "0":
            print(Fore.MAGENTA + "До свидания!")
            break
        
        elif choice == "1":
            url = input("Введите URL (полностью, включая https://): ").strip()
            if not url:
                print(Fore.RED + "URL не может быть пустым.")
                continue
            result = get(url)
            if result:
                print_json_pretty(result)
            else:
                print(Fore.RED + "Запрос не удался или вернул невалидный JSON.")
        
        elif choice == "2":
            country = input("Введите название страны на английском (например, Germany): ").strip()
            if not country:
                print(Fore.RED + "Название страны не может быть пустым.")
                continue
            display_country_info(country)
        
        elif choice == "3":
            get_random_dog()
        
        else:
            print(Fore.RED + "Неверный пункт меню. Пожалуйста, выберите 0, 1, 2 или 3.")

if __name__ == "__main__":
    main()