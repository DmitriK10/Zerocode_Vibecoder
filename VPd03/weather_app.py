"""
Модуль для получения погоды с OpenWeather API.
Использует безопасное хранение ключа в .env,
кэширование ответов, повторные попытки при сбоях,
поддержку ввода по городу или координатам.
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional, Any

import requests
from dotenv import load_dotenv

# Загружаем переменные окружения из .env (полный путь к файлу .env не нужен,
# dotenv ищет его в текущей рабочей директории)
load_dotenv()

# Глобально получаем API-ключ (принцип единственной ответственности – только загрузка)
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY не найден в .env файле. Проверьте настройки.")


class CacheManager:
    """Управление кэшированием ответов погоды в JSON-файл."""
    
    def __init__(self, cache_file: str = "weather_cache.json"):
        self.cache_file = cache_file
        self._ensure_cache_file()
    
    def _ensure_cache_file(self) -> None:
        """Создаёт пустой кэш-файл, если его нет."""
        if not os.path.exists(self.cache_file):
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump({}, f)
    
    def _load_cache(self) -> Dict:
        """Загружает данные кэша из файла."""
        with open(self.cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _save_cache(self, data: Dict) -> None:
        """Сохраняет данные кэша в файл."""
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get(self, city: str = None, lat: float = None, lon: float = None) -> Optional[Dict]:
        """
        Возвращает закэшированные данные для заданного города или координат,
        если они не старше 3 часов.
        """
        cache = self._load_cache()
        key = self._make_key(city, lat, lon)
        if key not in cache:
            return None
        
        entry = cache[key]
        fetched_at = datetime.fromisoformat(entry["fetched_at"])
        if datetime.now() - fetched_at > timedelta(hours=3):
            # Кэш устарел
            return None
        return entry["data"]
    
    def set(self, data: Dict, city: str = None, lat: float = None, lon: float = None) -> None:
        """Сохраняет данные в кэш с текущей временной меткой."""
        cache = self._load_cache()
        key = self._make_key(city, lat, lon)
        cache[key] = {
            "data": data,
            "fetched_at": datetime.now().isoformat(),
            "city": city,
            "lat": lat,
            "lon": lon
        }
        self._save_cache(cache)
    
    @staticmethod
    def _make_key(city: str = None, lat: float = None, lon: float = None) -> str:
        """Формирует уникальный ключ для кэша на основе города или координат."""
        if city:
            return f"city_{city.lower().strip()}"
        elif lat is not None and lon is not None:
            return f"coord_{lat}_{lon}"
        else:
            raise ValueError("Нужно указать либо city, либо (lat, lon)")


class OpenWeatherClient:
    """Клиент для HTTP-запросов к OpenWeather API с автоматическими повторными попытками."""
    
    BASE_URL_GEO = "https://api.openweathermap.org/geo/1.0/direct"
    BASE_URL_WEATHER = "https://api.openweathermap.org/data/2.5/weather"
    
    def __init__(self, api_key: str, max_retries: int = 3, backoff_factor: float = 1.0):
        self.api_key = api_key
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor  # начальная пауза 1с, затем 2с, 4с
    
    def _make_request(self, url: str, params: Dict) -> Optional[requests.Response]:
        """
        Выполняет GET-запрос с повторными попытками при 429 или временных ошибках.
        Возвращает объект Response при успехе, иначе None.
        """
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Too Many Requests
                    wait = self.backoff_factor * (2 ** attempt)
                    print(f"Слишком много запросов. Пауза {wait} сек...")
                    time.sleep(wait)
                    continue
                else:
                    # Другие ошибки (401, 404 и т.д.) не повторяем
                    print(f"Ошибка HTTP {response.status_code}: {response.text}")
                    return None
            except requests.exceptions.RequestException as e:
                print(f"Сетевая ошибка: {e}. Попытка {attempt+1} из {self.max_retries}")
                if attempt < self.max_retries - 1:
                    wait = self.backoff_factor * (2 ** attempt)
                    time.sleep(wait)
                else:
                    return None
        return None
    
    def get_coordinates(self, city: str) -> Optional[Tuple[float, float]]:
        """
        Получает широту и долготу по названию города (первый результат).
        Возвращает (lat, lon) или None.
        """
        params = {
            "q": city,
            "limit": 1,
            "appid": self.api_key,
            "lang": "ru"
        }
        response = self._make_request(self.BASE_URL_GEO, params)
        if not response:
            return None
        data = response.json()
        if not data:
            print(f"Город '{city}' не найден.")
            return None
        lat = data[0].get("lat")
        lon = data[0].get("lon")
        if lat is None or lon is None:
            print("Не удалось получить координаты из ответа.")
            return None
        return lat, lon
    
    def get_weather_by_coordinates(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Получает текущую погоду по координатам (температура в Цельсиях, описание на русском).
        Возвращает словарь с данными или None.
        """
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric",
            "lang": "ru"
        }
        response = self._make_request(self.BASE_URL_WEATHER, params)
        if not response:
            return None
        return response.json()


class WeatherService:
    """
    Сервис для получения погоды с использованием кэша и клиента API.
    Соблюдает принцип единственной ответственности: координирует кэш и API.
    """
    
    def __init__(self, api_client: OpenWeatherClient, cache_manager: CacheManager):
        self.api_client = api_client
        self.cache_manager = cache_manager
    
    def get_weather_by_city(self, city: str, use_cache: bool = True) -> Optional[Dict]:
        """Получает погоду по названию города, используя кэш при необходимости."""
        # Проверяем кэш
        if use_cache:
            cached = self.cache_manager.get(city=city)
            if cached:
                print("Используем кэшированные данные (менее 3 часов).")
                return cached
        
        # Запрос координат
        coords = self.api_client.get_coordinates(city)
        if not coords:
            return None
        lat, lon = coords
        
        # Запрос погоды
        weather = self.api_client.get_weather_by_coordinates(lat, lon)
        if weather:
            # Сохраняем в кэш
            self.cache_manager.set(weather, city=city, lat=lat, lon=lon)
        return weather
    
    def get_weather_by_coords(self, lat: float, lon: float, use_cache: bool = True) -> Optional[Dict]:
        """Получает погоду по координатам, используя кэш."""
        if use_cache:
            cached = self.cache_manager.get(lat=lat, lon=lon)
            if cached:
                print("Используем кэшированные данные (менее 3 часов).")
                return cached
        
        weather = self.api_client.get_weather_by_coordinates(lat, lon)
        if weather:
            self.cache_manager.set(weather, lat=lat, lon=lon)
        return weather


class CLI:
    """Консольный интерфейс для взаимодействия с пользователем."""
    
    def __init__(self, weather_service: WeatherService):
        self.service = weather_service
    
    @staticmethod
    def format_weather(weather_data: Dict) -> str:
        """Форматирует словарь с погодой в читаемую строку."""
        try:
            city_name = weather_data.get("name", "Неизвестный город")
            temp = weather_data["main"]["temp"]
            desc = weather_data["weather"][0]["description"]
            return f"Погода в {city_name}: {temp}°C, {desc}"
        except (KeyError, IndexError):
            return "Ошибка форматирования данных погоды."
    
    def run(self):
        """Главный цикл программы."""
        print("=== Погодное приложение (OpenWeather) ===")
        while True:
            print("\nВыберите режим:")
            print("1 — По названию города")
            print("2 — По координатам (широта, долгота)")
            print("0 — Выход")
            choice = input("Ваш выбор: ").strip()
            
            if choice == "0":
                print("До свидания!")
                break
            elif choice == "1":
                city = input("Введите название города: ").strip()
                if not city:
                    print("Город не может быть пустым.")
                    continue
                weather = self.service.get_weather_by_city(city)
                if weather:
                    print(self.format_weather(weather))
                else:
                    print("Не удалось получить погоду. Проверьте соединение или API-ключ.")
            elif choice == "2":
                try:
                    lat = float(input("Широта: "))
                    lon = float(input("Долгота: "))
                except ValueError:
                    print("Введите числовые значения координат.")
                    continue
                weather = self.service.get_weather_by_coords(lat, lon)
                if weather:
                    print(self.format_weather(weather))
                else:
                    print("Не удалось получить погоду. Проверьте соединение или API-ключ.")
            else:
                print("Неверный ввод. Пожалуйста, выберите 0, 1 или 2.")


def main():
    """Точка входа в программу."""
    # Создаём зависимости
    cache_mgr = CacheManager()
    api_client = OpenWeatherClient(API_KEY)
    weather_service = WeatherService(api_client, cache_mgr)
    cli = CLI(weather_service)
    cli.run()


if __name__ == "__main__":
    main()