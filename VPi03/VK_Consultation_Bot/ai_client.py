import aiohttp
import logging
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self, api_key: str, model: str, api_url: str):
        self.api_key = api_key
        self.model = model
        self.api_url = api_url

    async def generate_response(self, user_message: str) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Ты полезный ассистент для консультаций по IT."},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        error_text = await resp.text()
                        logger.error(f"Ошибка AI: статус {resp.status}, тело: {error_text[:200]}")
                        return None
        except aiohttp.ClientError as e:
            logger.error(f"Сетевая ошибка при запросе к AI: {e}")
            return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка в AI клиенте: {e}")
            return None