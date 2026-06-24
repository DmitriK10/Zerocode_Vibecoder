from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import openai
import requests
import logging

logger = logging.getLogger(__name__)

class APIClient(ABC):
    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]],
                          temperature: float = 0.7,
                          max_tokens: int = 1000,
                          model: Optional[str] = None) -> Dict[str, Any]:
        pass

class OpenAIClient(APIClient):
    def __init__(self, api_key: str, base_url: Optional[str] = None, default_model: str = 'gpt-3.5-turbo'):
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = openai.OpenAI(**client_kwargs)
        self.default_model = default_model

    def generate_response(self, messages: List[Dict[str, str]],
                          temperature: float = 0.7,
                          max_tokens: int = 1000,
                          model: Optional[str] = None) -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return {
                'content': response.choices[0].message.content,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

class GenAPIClient(APIClient):
    def __init__(self, api_key: str, base_url: str, default_model: str = 'gpt-3.5-turbo'):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.default_model = default_model

    def generate_response(self, messages: List[Dict[str, str]],
                          temperature: float = 0.7,
                          max_tokens: int = 1000,
                          model: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "is_sync": True
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            return {
                'content': result['choices'][0]['message']['content'],
                'usage': result.get('usage', {})
            }
        except Exception as e:
            logger.error(f"GenAPI error: {e}")
            raise

def create_api_client(config):
    if config.OPENAI_API_KEY:
        return OpenAIClient(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL,
            default_model=config.DEFAULT_MODEL
        )
    elif config.GENAPI_KEY:
        return GenAPIClient(
            api_key=config.GENAPI_KEY,
            base_url=config.GENAPI_URL,
            default_model=config.DEFAULT_MODEL
        )
    else:
        raise ValueError("Нет доступных API ключей")