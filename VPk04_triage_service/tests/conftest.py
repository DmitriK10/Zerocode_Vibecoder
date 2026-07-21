import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_triage_service
from app.llm.base import LLMClient
from app.repository.ticket_repo import TicketRepository
from app.services.rate_limiter import RateLimiter
from app.services.triage_service import TriageService


class MockLLMClient(LLMClient):
    """Заглушка LLM-клиента для тестов."""
    def __init__(self, fail=False):
        self.fail = fail
        self.last_text = None

    async def triage(self, text: str):
        self.last_text = text
        if self.fail:
            raise Exception("LLM error")
        return {
            "category": "billing",
            "draft_reply": "Тестовый ответ",
            "confidence": "high",
            "escalate": False,
        }


@pytest.fixture
def mock_llm():
    return MockLLMClient()


@pytest.fixture
def test_db():
    # Создаём временный файл БД и НЕ удаляем его (Windows блокирует)
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = TicketRepository(db_path=path)
    yield db
    # Для Windows не вызываем os.unlink, временная папка очистится сама позже


@pytest.fixture
def rate_limiter():
    return RateLimiter(max_requests=5)


@pytest.fixture
def triage_service(mock_llm, test_db, rate_limiter):
    return TriageService(
        llm_client=mock_llm,
        repository=test_db,
        rate_limiter=rate_limiter,
    )


@pytest.fixture
def client(triage_service):
    app.dependency_overrides[get_triage_service] = lambda: triage_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()