import aiohttp
import logging
import urllib.parse
from utils.retry import retry

logger = logging.getLogger(__name__)

@retry(max_attempts=3, delay=1.0)
async def generate_image(prompt: str, width: int = 512, height: int = 512) -> bytes:
    """
    Генерирует изображение через pollinations.ai.
    Возвращает байты PNG.
    """
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