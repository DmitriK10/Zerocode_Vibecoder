import json
import logging
import re
import httpx
from openai import OpenAI
from app.models import StructuredResponse
from app.config import Config

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self, api_key: str, base_url: str, model: str, http_proxy: str = None, https_proxy: str = None):
        proxies = {}
        if http_proxy:
            proxies["http://"] = http_proxy
        if https_proxy:
            proxies["https://"] = https_proxy
        http_client = httpx.Client(proxies=proxies) if proxies else None

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=http_client
        )
        self.model = model

    def _extract_content(self, raw_response) -> str:
        """Извлекает текстовое содержимое из ответа API в любом формате."""
        if hasattr(raw_response, 'choices') and raw_response.choices:
            return raw_response.choices[0].message.content
        if isinstance(raw_response, list):
            if raw_response and isinstance(raw_response[-1], dict) and 'content' in raw_response[-1]:
                return raw_response[-1]['content']
            elif raw_response and isinstance(raw_response[-1], str):
                return raw_response[-1]
        if isinstance(raw_response, dict):
            if 'error' in raw_response:
                error_msg = raw_response['error'].get('message', str(raw_response['error']))
                return f"Ошибка API: {error_msg}"
            if 'message' in raw_response and 'status_code' in raw_response:
                return f"Ошибка {raw_response.get('status_code')}: {raw_response.get('message', '')}"
            if 'data' in raw_response and isinstance(raw_response['data'], list):
                if raw_response['data']:
                    last = raw_response['data'][-1]
                    if isinstance(last, dict) and 'content' in last:
                        return last['content']
                    elif isinstance(last, str):
                        return last
            if 'message' in raw_response:
                return str(raw_response['message'])
            if 'content' in raw_response:
                return str(raw_response['content'])
            for key in ['text', 'response', 'result']:
                if key in raw_response:
                    return str(raw_response[key])
        return str(raw_response)

    def _is_error_response(self, raw_response) -> bool:
        if hasattr(raw_response, 'status_code') and raw_response.status_code >= 400:
            return True
        if isinstance(raw_response, dict):
            if 'error' in raw_response:
                return True
            if 'status_code' in raw_response and raw_response['status_code'] >= 400:
                return True
        return False

    def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        history: list = None
    ) -> StructuredResponse:
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=3000,
                temperature=0.7
            )

            raw = response
            logger.debug("Сырой ответ (тип %s): %s", type(raw), raw)

            if self._is_error_response(raw):
                error_content = self._extract_content(raw)
                logger.error("API вернул ошибку: %s", error_content)
                return StructuredResponse(
                    theses=[],
                    message=f"⚠️ Сервис временно недоступен. Причина: {error_content}"
                )

            content = self._extract_content(raw)
            logger.debug("Извлечённый контент: %s", content)

            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                else:
                    json_str = content

            data = json.loads(json_str)
            theses = data.get("theses", [])
            message = data.get("message", content)
            if not isinstance(theses, list):
                theses = [str(theses)] if theses else []
            return StructuredResponse(theses=theses, message=message)

        except json.JSONDecodeError as e:
            logger.warning("Ответ модели не является JSON (будет отправлен как обычный текст): %s", e)
            try:
                fallback_content = self._extract_content(response) if 'response' in locals() else content
            except:
                fallback_content = "Извините, произошла ошибка при обработке ответа."
            return StructuredResponse(
                theses=[],   # <-- исправлено: пустой список вместо попытки извлечь тезисы
                message=fallback_content
            )
        except Exception as e:
            logger.error("Ошибка при генерации: %s", e)
            try:
                fallback_content = self._extract_content(response) if 'response' in locals() else str(e)
            except:
                fallback_content = "Извините, произошла ошибка. Попробуйте позже."
            return StructuredResponse(
                theses=[],   # <-- исправлено: больше не сохраняем "Ошибка генерации"
                message=fallback_content
            )