"""
Тесты сервиса взаимодействия с GPT-прокси (GPTProxyService).

Проверяют:
- успешный ответ от GPT (статус 200)
- обработку ошибок HTTP (статус 400)
"""

import pytest
from unittest.mock import AsyncMock, Mock
import httpx
from app.services.gpt_proxy_service import GPTProxyService


@pytest.mark.asyncio
async def test_generate_response_success():
    """
    Проверяет успешный ответ от GPT-прокси.

    Мокируется клиент, имитирующий успешный HTTP-ответ 200 с корректным JSON.
    Ожидается:
    - возврат текста анализа из ответа
    - метод post был вызван ровно один раз
    """
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json = Mock(return_value={
        "choices": [{"message": {"content": "Test analysis"}}]
    })
    mock_client.post = AsyncMock(return_value=mock_response)

    service = GPTProxyService(http_client=mock_client)
    result = await service.generate_response("Test prompt")
    assert result == "Test analysis"
    mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_generate_response_http_error():
    """
    Проверяет обработку HTTP-ошибки со стороны GPT-прокси.

    Мокируется клиент, возвращающий статус 400 (Bad Request).
    Ожидается:
    - генерация исключения RuntimeError с текстом, содержащим "GPT proxy error"
    """
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Bad Request", request=None, response=mock_response
    )
    mock_client.post = AsyncMock(return_value=mock_response)

    service = GPTProxyService(http_client=mock_client)
    with pytest.raises(RuntimeError, match="GPT proxy error"):
        await service.generate_response("Test")