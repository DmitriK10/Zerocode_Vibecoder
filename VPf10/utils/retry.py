import asyncio
import logging
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)

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