import os
import re
import time
import json
import ast
import operator
import requests
import qrcode
from duckduckgo_search import DDGS

# Импортируем функции работы с БД (для фильмов)
from .db import (
    list_movies as db_list_movies,
    find_movie_by_title as db_find_title,
    find_movies_by_director as db_find_director,
    find_movies_by_genre as db_find_genre,
    add_movie as db_add_movie,
    delete_movie as db_delete_movie,
    update_movie_rating as db_update_rating,
    get_top_movies as db_top_movies,
    get_random_movie as db_random_movie
)

# ---------- Инструменты для работы с фильмами ----------
def list_movies():
    """Возвращает список всех фильмов."""
    return db_list_movies()

def find_movie_by_title(title: str):
    """Поиск фильмов по части названия."""
    return db_find_title(title)

def find_movies_by_director(director: str):
    """Поиск фильмов по части имени режиссёра."""
    return db_find_director(director)

def find_movies_by_genre(genre: str):
    """Поиск фильмов по жанру (точное совпадение)."""
    return db_find_genre(genre)

def add_movie(title: str, director: str, genre: str, year: int = None, rating: float = None):
    """Добавляет новый фильм."""
    return db_add_movie(title, director, genre, year, rating)

def delete_movie(movie_id: int):
    """Удаляет фильм по ID."""
    success = db_delete_movie(movie_id)
    if success:
        return f"Фильм с id={movie_id} успешно удалён."
    else:
        return f"Фильм с id={movie_id} не найден."

def update_movie_rating(movie_id: int, new_rating: float):
    """Обновляет рейтинг фильма."""
    updated = db_update_rating(movie_id, new_rating)
    if updated:
        return f"Рейтинг фильма '{updated['title']}' обновлён до {new_rating}."
    else:
        return f"Фильм с id={movie_id} не найден."

def get_top_movies(limit: int = 5):
    """
    Возвращает топ-N фильмов по рейтингу в виде отформатированной строки.
    Это исключение сделано для удобства пользователя – он видит красивый список сразу.
    """
    movies = db_top_movies(limit)
    if not movies:
        return "Нет фильмов для отображения."
    lines = [f"🎬 Топ-{limit} фильмов по рейтингу:"]
    for i, m in enumerate(movies, 1):
        lines.append(f"{i}. {m['title']} ({m['year']}) – рейтинг: {m['rating']} (реж. {m['director']}, жанр: {m['genre']})")
    return "\n".join(lines)

def get_random_movie():
    """Возвращает случайный фильм."""
    movie = db_random_movie()
    if movie:
        return (f"🎲 Случайный фильм:\n"
                f"Название: {movie['title']}\n"
                f"Режиссёр: {movie['director']}\n"
                f"Жанр: {movie['genre']}\n"
                f"Год: {movie['year']}\n"
                f"Рейтинг: {movie['rating']}")
    else:
        return "В базе нет фильмов."

# ---------- Безопасный калькулятор (без eval) ----------
def _safe_eval(expr: str) -> float:
    """
    Безопасно вычисляет арифметическое выражение, используя AST-парсинг.
    Поддерживает: +, -, *, /, **, ( ), числа (целые и с плавающей точкой).
    """
    # Убираем пробелы и проверяем допустимые символы
    expr = expr.replace(" ", "")
    if not re.match(r'^[\d+\-*/().]+$', expr):
        raise ValueError("Недопустимые символы в выражении")

    # Парсим AST
    tree = ast.parse(expr, mode='eval')
    # Проверяем, что в дереве только разрешённые узлы
    allowed_nodes = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Constant)
    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise ValueError("Недопустимая конструкция в выражении")
        if isinstance(node, ast.BinOp):
            if not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
                raise ValueError("Недопустимая операция")
        if isinstance(node, ast.UnaryOp):
            if not isinstance(node.op, (ast.UAdd, ast.USub)):
                raise ValueError("Недопустимая унарная операция")

    # Вычисляем с помощью operator
    def eval_node(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Num):  # для совместимости со старыми версиями
            return node.n
        if isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            ops = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
            }
            return ops[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp):
            operand = eval_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand
        raise ValueError("Неизвестный узел")

    return eval_node(tree.body)

def calculate(expression: str):
    """Безопасное вычисление математического выражения (поддерживает +, -, *, /, **, (, ))."""
    try:
        result = _safe_eval(expression)
        return f"Результат: {result}"
    except Exception as e:
        return f"Ошибка вычисления: {str(e)}"

# ---------- Погода ----------
def get_weather(city: str):
    """Получить текущую погоду для города через Open-Meteo."""
    try:
        geocode_url = "https://nominatim.openstreetmap.org/search"
        params = {"q": city, "format": "json", "limit": 1}
        headers = {"User-Agent": "MCP-Server/1.0"}
        resp = requests.get(geocode_url, params=params, headers=headers, timeout=10)
        if resp.status_code != 200:
            return "Не удалось определить координаты города (сервис геокодинга временно недоступен)."
        data = resp.json()
        if not data:
            return f"Город '{city}' не найден."
        lat = float(data[0]['lat'])
        lon = float(data[0]['lon'])

        weather_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "timezone": "auto"
        }
        resp = requests.get(weather_url, params=params, timeout=10)
        if resp.status_code != 200:
            return "Не удалось получить данные о погоде (сервис погоды временно недоступен)."
        w = resp.json().get("current_weather", {})
        temp = w.get("temperature")
        wind = w.get("windspeed")
        weather_code = w.get("weathercode")

        conditions = {
            0: "Ясно", 1: "Преимущественно ясно", 2: "Переменная облачность", 3: "Пасмурно",
            45: "Туман", 48: "Туман с изморозью",
            51: "Морось слабая", 53: "Морось умеренная", 55: "Морось сильная",
            61: "Дождь слабый", 63: "Дождь умеренный", 65: "Дождь сильный",
            80: "Ливень слабый", 81: "Ливень умеренный", 82: "Ливень сильный",
            95: "Гроза", 96: "Гроза с градом", 99: "Гроза с сильным градом"
        }
        cond = conditions.get(weather_code, "Неизвестно")
        return (f"Погода в городе {city}:\n"
                f"Температура: {temp}°C\n"
                f"Скорость ветра: {wind} км/ч\n"
                f"Условия: {cond}")
    except Exception as e:
        return f"Ошибка получения погоды: {str(e)}"

# ---------- Курс валют ----------
def get_exchange_rate(from_currency: str, to_currency: str = "RUB"):
    """Получить курс обмена между двумя валютами."""
    try:
        url = f"https://api.exchangerate.host/latest?base={from_currency.upper()}&symbols={to_currency.upper()}"
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return f"Ошибка API: статус {resp.status_code}"
        data = resp.json()
        if not data.get("success", False):
            return "Не удалось получить курс. Проверьте правильность кодов валют."
        rate = data["rates"].get(to_currency.upper())
        if rate is None:
            return f"Валюта '{to_currency}' не поддерживается."
        return f"Курс 1 {from_currency.upper()} = {rate} {to_currency.upper()}"
    except Exception as e:
        return f"Ошибка получения курса: {str(e)}"

# ---------- Генерация QR-кода ----------
def generate_qr(data: str, filename: str = None):
    """Генерирует QR-код из текста и сохраняет в PNG. Возвращает путь к файлу."""
    try:
        safe_name = re.sub(r'[^\w\-_.]', '', data[:20].replace(' ', '_'))
        if not safe_name:
            safe_name = "qr_code"
        timestamp = int(time.time())
        if filename is None:
            filename = f"qr_{safe_name}_{timestamp}.png"
        elif not filename.lower().endswith('.png'):
            filename += '.png'
        img = qrcode.make(data)
        img.save(filename)
        abs_path = os.path.abspath(filename)
        return f"✅ QR-код сохранён: {abs_path}"
    except Exception as e:
        return f"❌ Ошибка генерации QR-кода: {str(e)}"

# ---------- Поиск в интернете (DuckDuckGo) ----------
def web_search(query: str):
    """Поиск информации через DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if not results:
                return "По вашему запросу ничего не найдено."
            answer = "\n".join([f"{i+1}. {r['title']}: {r['body']}" for i, r in enumerate(results)])
            return answer
    except Exception as e:
        return f"Ошибка поиска: {str(e)}"

# ---------- MCP-описание инструментов (JSON Schema) ----------
MCP_TOOLS = [
    {
        "name": "list_movies",
        "description": "Возвращает список всех фильмов из базы данных",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "find_movie_by_title",
        "description": "Находит фильмы по частичному совпадению названия",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Часть названия фильма"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "find_movies_by_director",
        "description": "Находит фильмы по частичному совпадению имени режиссёра",
        "inputSchema": {
            "type": "object",
            "properties": {
                "director": {"type": "string", "description": "Имя режиссёра (или часть)"}
            },
            "required": ["director"]
        }
    },
    {
        "name": "find_movies_by_genre",
        "description": "Находит фильмы по жанру (точное совпадение)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "genre": {"type": "string", "description": "Жанр фильма (например, Драма)"}
            },
            "required": ["genre"]
        }
    },
    {
        "name": "add_movie",
        "description": "Добавляет новый фильм в базу данных",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Название фильма"},
                "director": {"type": "string", "description": "Режиссёр"},
                "genre": {"type": "string", "description": "Жанр"},
                "year": {"type": "integer", "description": "Год выпуска (необязательно)"},
                "rating": {"type": "number", "description": "Рейтинг (необязательно)"}
            },
            "required": ["title", "director", "genre"]
        }
    },
    {
        "name": "delete_movie",
        "description": "Удаляет фильм по его ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "movie_id": {"type": "integer", "description": "ID фильма"}
            },
            "required": ["movie_id"]
        }
    },
    {
        "name": "update_movie_rating",
        "description": "Обновляет рейтинг фильма",
        "inputSchema": {
            "type": "object",
            "properties": {
                "movie_id": {"type": "integer", "description": "ID фильма"},
                "new_rating": {"type": "number", "description": "Новое значение рейтинга"}
            },
            "required": ["movie_id", "new_rating"]
        }
    },
    {
        "name": "get_top_movies",
        "description": "Возвращает топ-N фильмов по рейтингу (по умолчанию 5) в удобочитаемом виде",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Количество фильмов (необязательно, по умолчанию 5)"}
            },
            "required": []
        }
    },
    {
        "name": "get_random_movie",
        "description": "Возвращает случайный фильм из базы",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    # Остальные старые инструменты
    {
        "name": "calculate",
        "description": "Вычисляет математическое выражение (поддерживает +, -, *, /, **, (, ))",
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Математическое выражение"}
            },
            "required": ["expression"]
        }
    },
    {
        "name": "get_weather",
        "description": "Получает текущую погоду для указанного города",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "Название города"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "get_exchange_rate",
        "description": "Получает курс обмена между двумя валютами (по умолчанию к RUB)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_currency": {"type": "string", "description": "Код базовой валюты (например, USD)"},
                "to_currency": {"type": "string", "description": "Код целевой валюты (например, RUB), необязательно"}
            },
            "required": ["from_currency"]
        }
    },
    {
        "name": "generate_qr",
        "description": "Генерирует QR-код из переданного текста и сохраняет в PNG файл",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Текст для кодирования в QR-код"},
                "filename": {"type": "string", "description": "Имя файла (необязательно)"}
            },
            "required": ["data"]
        }
    },
    {
        "name": "web_search",
        "description": "Выполняет поиск в интернете по заданному запросу (DuckDuckGo)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Поисковый запрос"}
            },
            "required": ["query"]
        }
    }
]

# Маппинг имени инструмента на функцию
TOOL_FUNCTIONS = {
    "list_movies": list_movies,
    "find_movie_by_title": find_movie_by_title,
    "find_movies_by_director": find_movies_by_director,
    "find_movies_by_genre": find_movies_by_genre,
    "add_movie": add_movie,
    "delete_movie": delete_movie,
    "update_movie_rating": update_movie_rating,
    "get_top_movies": get_top_movies,
    "get_random_movie": get_random_movie,
    "calculate": calculate,
    "get_weather": get_weather,
    "get_exchange_rate": get_exchange_rate,
    "generate_qr": generate_qr,
    "web_search": web_search
}