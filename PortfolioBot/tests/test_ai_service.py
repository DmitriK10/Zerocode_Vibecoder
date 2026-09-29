import pytest
from src.ai_service import ProxyOpenAIClient
from unittest.mock import patch, MagicMock
import httpx

def test_proxy_client_success():
    client = ProxyOpenAIClient(api_key="test_key")
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "AI Response"}}]
    }
    with patch.object(client._client, 'post', return_value=mock_response) as mock_post:
        result = client.ask("Hello")
        assert result == "AI Response"
        mock_post.assert_called_once()

def test_proxy_client_http_error():
    client = ProxyOpenAIClient(api_key="test_key")
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 500
    # ИСПРАВЛЕНИЕ: Явно задаем text как строку, чтобы срез [:200] в коде работал
    mock_response.text = '{"error": {"message": "Internal Server Error"}}'
    
    mock_request = MagicMock(spec=httpx.Request)
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error", request=mock_request, response=mock_response
    )
    
    with patch.object(client._client, 'post', return_value=mock_response):
        result = client.ask("Hello")
        # Проверяем, что код вернул строку с кодом ошибки, а не упал
        assert "Ошибка 500" in result