import os
import httpx
from src.interfaces import LLMAssistantInterface

class ProxyOpenAIClient(LLMAssistantInterface):
    def __init__(self, api_key: str):
        self._api_key = api_key
        self._base_url = os.getenv("AI_BASE_URL", "https://api.proxyapi.ru/openai/v1")
        proxy_url = os.getenv("AI_PROXY_URL")
        
        print(f"DEBUG AI: Base URL = {self._base_url}")
        print(f"DEBUG AI: Proxy URL = {proxy_url or 'None'}")
        print(f"DEBUG AI: API Key starts with = {self._api_key[:10]}...")
        
        self._client = httpx.Client(proxy=proxy_url, timeout=15.0) if proxy_url else httpx.Client(timeout=15.0)

    def ask(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Ты - профессиональный ассистент Python-разработчика. Отвечай кратко и по делу."},
                {"role": "user", "content": prompt}
            ]
        }
        
        url = f"{self._base_url}/chat/completions"
        print(f"DEBUG AI: Request URL = {url}")
        
        try:
            response = self._client.post(url, json=payload, headers=headers)
            print(f"DEBUG AI: Status = {response.status_code}")
            print(f"DEBUG AI: Response = {response.text[:300]}")
            
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except httpx.ConnectError as e:
            return f"⚠️ Ошибка сети: не удалось подключиться. (Детали: {e})"
        except httpx.HTTPStatusError as e:
            return f"⚠️ Ошибка {e.response.status_code}: {e.response.text[:200]}"
        except Exception as e:
            return f"⚠️ Неизвестная ошибка: {str(e)}"