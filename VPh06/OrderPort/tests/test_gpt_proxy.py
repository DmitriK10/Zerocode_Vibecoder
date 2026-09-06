"""
Тесты сервиса взаимодействия с GPT-прокси (GPTProxyService).
"""

import pytest
from unittest.mock import AsyncMock, Mock
import httpx
from app.services.gpt_proxy_service import GPTProxyService


@pytest.mark.asyncio
async def test_generate_response_success():
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


def test_model_restriction():
    """Проверяем, что если модель выше gpt-3.5-turbo-16k, выбрасывается ValueError."""
    from app.config import settings
    # Временно меняем модель
    original = settings.OPENAI_MODEL
    settings.OPENAI_MODEL = "gpt-4"
    try:
        with pytest.raises(ValueError, match="gpt-3.5-turbo-16k"):
            GPTProxyService()
    finally:
        settings.OPENAI_MODEL = original