import asyncio
import aiohttp
import requests
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, Dict, Any

logger = logging.getLogger(__name__)

# ---------- Кэш для курса валют ----------
_cache_usd_rate: Dict[str, Any] = {
    "rate": 100.0,
    "updated_at": datetime.min
}
CACHE_TTL = timedelta(minutes=10)

# ---------- Декоратор повторных попыток ----------
def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"Превышено число попыток для {func.__name__}: {e}")
                        raise
                    logger.warning(f"Попытка {attempt} для {func.__name__} не удалась: {e}. Повтор через {current_delay}с")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            return None
        return async_wrapper
    return decorator

# ---------- Генерация изображений ----------
@retry(max_attempts=3, delay=1.0)
async def generate_image(prompt: str, width: int = 512, height: int = 512) -> bytes:
    """
    Генерирует изображение по текстовому запросу через image.pollinations.ai.
    Возвращает байты PNG-изображения.
    """
    import urllib.parse
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
    headers = {
        "Accept": "image/png,image/*;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=30) as response:
                response.raise_for_status()
                content_type = response.headers.get('Content-Type', '')
                logger.debug(f"Content-Type: {content_type}, размер: {response.content_length}")
                if not content_type.startswith('image/'):
                    text = await response.text()
                    raise ValueError(f"Ответ не является изображением. Content-Type: {content_type}, тело: {text[:200]}")
                return await response.read()
    except aiohttp.ClientError as e:
        logger.error(f"Ошибка при запросе к pollinations.ai: {e}")
        raise

# ---------- Курс валют с кэшированием ----------
def get_usd_rub_rate() -> float:
    """Получает курс USD/RUB от ЦБ РФ с кэшированием на 10 минут."""
    global _cache_usd_rate
    now = datetime.now()
    if now - _cache_usd_rate["updated_at"] < CACHE_TTL:
        logger.debug(f"Используем кэшированный курс: {_cache_usd_rate['rate']}")
        return _cache_usd_rate["rate"]

    try:
        today = datetime.now().strftime("%d/%m/%Y")
        url = f"https://www.cbr.ru/scripts/XML_daily.asp?date_req={today}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        for valute in root.findall("Valute"):
            if valute.find("CharCode").text == "USD":
                value = valute.find("Value").text.replace(",", ".")
                rate = float(value)
                _cache_usd_rate["rate"] = rate
                _cache_usd_rate["updated_at"] = now
                logger.debug(f"Обновлён курс: {rate}")
                return rate
        # Если USD не найден, возвращаем 100
        rate = 100.0
        _cache_usd_rate["rate"] = rate
        _cache_usd_rate["updated_at"] = now
        return rate
    except Exception as e:
        logger.error(f"Ошибка получения курса ЦБ: {e}")
        # Возвращаем кэшированное значение, даже если оно устарело
        return _cache_usd_rate["rate"]

def calculate_cost(usage: dict) -> dict:
    """
    Рассчитывает стоимость запроса в USD и RUB.
    usage: dict с ключами 'prompt_tokens', 'completion_tokens', 'total_tokens'
    """
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", 0)

    # Цены за 1000 токенов (в USD) – можно вынести в конфиг
    input_price_per_1k = 0.00015
    output_price_per_1k = 0.0006

    cost_usd = (input_tokens / 1000) * input_price_per_1k + (output_tokens / 1000) * output_price_per_1k
    rate = get_usd_rub_rate()
    cost_rub = cost_usd * rate

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cost_usd": cost_usd,
        "cost_rub": cost_rub,
        "rate_rub": rate
    }