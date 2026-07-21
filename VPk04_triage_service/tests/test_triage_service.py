import pytest
from app.models.schemas import TriageRequest
from app.core.exceptions import RateLimitExceededError


@pytest.mark.anyio
async def test_successful_triage(triage_service, mock_llm):
    request = TriageRequest(
        text="Проблема с оплатой",
        channel="email",
        client_id="123",
    )
    response = await triage_service.process(request)
    assert response.category == "billing"
    assert response.draft_reply == "Тестовый ответ"
    assert response.confidence == "high"
    assert response.escalate == False


@pytest.mark.anyio
async def test_fallback_on_llm_error(test_db, rate_limiter):
    from app.llm.base import LLMClient
    from app.services.triage_service import TriageService

    class FailingLLMClient(LLMClient):
        async def triage(self, text: str):
            raise Exception("LLM error")

    service = TriageService(FailingLLMClient(), test_db, rate_limiter)
    request = TriageRequest(
        text="Текст",
        channel="chat",
        client_id="42",
    )
    response = await service.process(request)
    assert response.escalate == True
    assert response.draft_reply == "передано оператору"
    assert response.confidence == "low"
    assert response.category == "other"


@pytest.mark.anyio
async def test_rate_limit_exceeded(triage_service, mock_llm):
    request = TriageRequest(text="msg", channel="form", client_id="limited")
    for _ in range(5):
        await triage_service.process(request)
    with pytest.raises(RateLimitExceededError):
        await triage_service.process(request)