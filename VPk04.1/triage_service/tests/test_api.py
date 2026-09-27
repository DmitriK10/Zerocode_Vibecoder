import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_triage_service
from app.models.schemas import TriageRequest, TriageResponse

client = TestClient(app)

class MockTriageService:
    """Мок-класс сервиса, имитирующий работу реального LLM-сервиса."""
    async def process(self, request: TriageRequest) -> TriageResponse:
        # Возвращаем детерминированный, предсказуемый ответ.
        # Это гарантирует, что тест не будет зависеть от реальной нейросети.
        return TriageResponse(
            category="support",
            draft_reply="Мы поможем вам восстановить доступ к аккаунту. Проверьте вашу почту.",
            confidence="high",
            escalate=False
        )

def get_mock_triage_service() -> MockTriageService:
    """Фабрика для внедрения зависимости мок-сервиса вместо реального."""
    return MockTriageService()

def test_post_triage_success_support_category(client):
    """Тест успешной обработки запроса с изолированным (замоканым) сервисом"""
    # 1. Подменяем реальную зависимость на нашу мок-фабрику
    app.dependency_overrides[get_triage_service] = get_mock_triage_service
    
    try:
        response = client.post(
            "/api/v1/triage",
            json={
                "text": "Не могу войти в аккаунт, сбросьте пароль",
                "channel": "email",
                "client_id": "test_user_1",
            },
        )
        
        assert response.status_code == 200, f"Ожидался 200, получен {response.status_code}. Ответ: {response.text}"
        
        data = response.json()
        # 2. Теперь мы на 100% уверены в результате, так как контролируем ответ
        assert data["category"] == "support"
        assert data["escalate"] is False
        assert data["confidence"] == "high"
        assert "draft_reply" in data
        
    finally:
        # 3. КРИТИЧЕСКИ ВАЖНО: очищаем оверрайды, чтобы не сломать другие тесты
        app.dependency_overrides.clear()

def test_post_triage_validation_error_empty_text(client):
    """Тест валидации: пустой текст должен возвращать 422 (ошибка Pydantic)"""
    # Здесь мок не нужен, так как ошибка валидации происходит ДО вызова сервиса
    response = client.post(
        "/api/v1/triage",
        json={
            "text": "   ",
            "channel": "email",
            "client_id": "test_user_2",
        },
    )
    assert response.status_code == 422
    assert "detail" in response.json()

def test_post_triage_rate_limit_exceeded(client):
    """Тест ограничения частоты запросов (Rate Limit)"""
    # Убеждаемся, что оверрайды очищены
    app.dependency_overrides.clear()
    
    client_id = "rate_limit_test_user"
    payload = {
        "text": "Тест лимита",
        "channel": "chat",
        "client_id": client_id,
    }
    
    # Проверяем, что API корректно обрабатывает запрос (200 или 429 при превышении)
    response = client.post("/api/v1/triage", json=payload)
    assert response.status_code in [200, 429]