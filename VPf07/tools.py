import os
import subprocess
import requests
import qrcode
import re
import time
from duckduckgo_search import DDGS
from langchain.tools import tool

# ---------- Поиск в интернете ----------
@tool
def web_search(query: str) -> str:
    """Поиск информации в интернете через DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if not results:
                return "По вашему запросу ничего не найдено."
            answer = "\n".join([f"{i+1}. {r['title']}: {r['body']}" for i, r in enumerate(results)])
            return answer
    except Exception as e:
        return f"Ошибка поиска: {str(e)}"

# ---------- Погода ----------
@tool
def get_weather(city: str) -> str:
    """Получить текущую погоду для города."""
    try:
        geocode_url = "https://nominatim.openstreetmap.org/search"
        params = {"q": city, "format": "json", "limit": 1}
        headers = {"User-Agent": "AI-Agent/1.0"}
        resp = requests.get(geocode_url, params=params, headers=headers, timeout=10)
        if resp.status_code != 200:
            return "Не удалось определить координаты города."
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
            return "Не удалось получить данные о погоде."
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

# ---------- Курс криптовалют ----------
@tool
def get_crypto_price(coin: str, currency: str = "usd") -> str:
    """Получить текущую цену криптовалюты в указанной валюте."""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies={currency}"
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return f"Ошибка API: статус {resp.status_code}"
        data = resp.json()
        if coin not in data:
            return f"Криптовалюта '{coin}' не найдена."
        price = data[coin].get(currency)
        if price is None:
            return f"Валюта '{currency}' не поддерживается для {coin}."
        return f"Текущая цена 1 {coin.upper()} составляет {price} {currency.upper()}"
    except Exception as e:
        return f"Ошибка получения курса: {str(e)}"

# ---------- Курс обычных валют ----------
@tool
def get_exchange_rate(from_currency: str, to_currency: str = "rub") -> str:
    """Получить курс обмена между двумя валютами (например, USD to RUB)."""
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
        return f"Ошибка получения курса валют: {str(e)}"

# ---------- Генерация QR-кода ----------
@tool
def generate_qr(data: str, filename: str = None) -> str:
    """
    Сгенерировать QR-код из текстовых данных и сохранить в файл PNG.
    Если filename не указан, создаётся имя автоматически с временной меткой.
    Возвращает полный путь к файлу и сообщение об успехе.
    """
    try:
        import qrcode
        from PIL import Image
    except ImportError:
        return "❌ Ошибка: не установлены библиотеки qrcode или Pillow. Установите: pip install qrcode Pillow"

    try:
        safe_name = data[:20].replace(" ", "_").replace("/", "_").replace("\\", "_")
        safe_name = re.sub(r'[^\w\-_.]', '', safe_name)
        if not safe_name:
            safe_name = "qr_code"
        timestamp = int(time.time())
        if filename is None:
            filename = f"qr_{safe_name}_{timestamp}.png"
        else:
            if not filename.lower().endswith('.png'):
                filename += '.png'

        img = qrcode.make(data)
        img.save(filename)
        abs_path = os.path.abspath(filename)
        return f"✅ QR-код успешно сгенерирован и сохранён в файл:\n`{abs_path}`"
    except Exception as e:
        return f"❌ Ошибка генерации QR-кода: {str(e)}"

# ---------- Чтение файла ----------
@tool
def file_read(file_path: str) -> str:
    """Прочитать содержимое текстового файла."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"Файл '{file_path}' не найден."
    except Exception as e:
        return f"Ошибка чтения файла: {str(e)}"

# ---------- Запись файла ----------
@tool
def file_write(file_path: str, content: str) -> str:
    """Записать содержимое в файл (перезапись)."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Файл '{file_path}' успешно записан."
    except Exception as e:
        return f"Ошибка записи файла: {str(e)}"

# ---------- Выполнение команд (улучшена для Windows) ----------
@tool
def run_command(command: str) -> str:
    """
    Выполнить команду в терминале.
    Поддерживаются: ls/dir, pwd/cd, echo, whoami, date/time, uptime (на Windows через systeminfo).
    """
    # Нормализуем команду для Windows
    cmd_lower = command.strip().lower()
    
    # Маппинг команд для Windows
    if cmd_lower.startswith('ls'):
        command = command.replace('ls', 'dir', 1)
    elif cmd_lower.startswith('pwd'):
        command = command.replace('pwd', 'echo %cd%', 1)
    elif cmd_lower.startswith('date'):
        if cmd_lower == 'date' or cmd_lower.startswith('date '):
            command = command.replace('date', 'date /t', 1)
    elif cmd_lower.startswith('uptime'):
        command = 'wmic os get lastbootuptime'

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            encoding='cp866'
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            if cmd_lower.startswith('uptime'):
                import re
                match = re.search(r'(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})\.\d+', output)
                if match:
                    year, month, day, hour, minute, second = match.groups()
                    boot_time = f"{day}.{month}.{year} {hour}:{minute}:{second}"
                    return f"Система загружена с: {boot_time}"
                else:
                    return output
            return output if output else "Команда выполнена (вывод пуст)"
        else:
            error = result.stderr.strip()
            return f"Ошибка выполнения: {error if error else 'неизвестная ошибка'}"
    except subprocess.TimeoutExpired:
        return "Ошибка: команда выполнялась слишком долго и была прервана."
    except Exception as e:
        return f"Ошибка выполнения команды: {str(e)}"

# Список всех инструментов
tools = [
    web_search,
    get_weather,
    get_crypto_price,
    get_exchange_rate,
    generate_qr,
    file_read,
    file_write,
    run_command
]