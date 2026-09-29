import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message
from src.bot_handlers import PortfolioBotHandlers
from src.interfaces import ProjectRepositoryInterface, LLMAssistantInterface

class MockRepo(ProjectRepositoryInterface):
    def __init__(self, data):
        self._data = data
    def get_projects(self):
        return self._data

class MockAI(LLMAssistantInterface):
    def ask(self, prompt: str) -> str:
        return "AI Mock Response"

@pytest.fixture
def mock_message():
    msg = MagicMock(spec=Message)
    msg.answer = AsyncMock()
    return msg

@pytest.mark.asyncio
async def test_cmd_projects_empty(mock_message):
    repo = MockRepo([])
    ai = MockAI()
    handlers = PortfolioBotHandlers(repo, ai)
    
    await handlers.cmd_projects(mock_message)
    mock_message.answer.assert_called_once_with("⚠️ Пока нет загруженных проектов.")

@pytest.mark.asyncio
async def test_cmd_projects_renders_html(mock_message):
    # ИСПРАВЛЕНИЕ: Убраны лишние пробелы в ключах и значениях
    data = [{
        "title": "Test Bot", "role": "Dev", "description": "Desc", 
        "stack": ["Python"], "features": ["Fast"], "link": "http://test", "status": "Done"
    }]
    repo = MockRepo(data)
    ai = MockAI()
    handlers = PortfolioBotHandlers(repo, ai)
    
    await handlers.cmd_projects(mock_message)
    
    call_args = mock_message.answer.call_args
    # ИСПРАВЛЕНИЕ: Проверяем HTML, так как мы перешли на него для надежности
    assert call_args.kwargs["parse_mode"] == "HTML"
    assert "Test Bot" in call_args.args[0]
    assert "<code>Python</code>" in call_args.args[0]