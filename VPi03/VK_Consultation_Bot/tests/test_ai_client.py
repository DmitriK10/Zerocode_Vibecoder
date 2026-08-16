import pytest
from unittest.mock import AsyncMock, patch
from ai_client import AIClient

@pytest.mark.asyncio
async def test_generate_response_success():
    client = AIClient(api_key="test", model="test", api_url="http://test")
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        result = await client.generate_response("Hello")
        assert result == "Test response"

@pytest.mark.asyncio
async def test_generate_response_fail():
    client = AIClient(api_key="test", model="test", api_url="http://test")
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_post.return_value.__aenter__.return_value = mock_response
        result = await client.generate_response("Hello")
        assert result is None