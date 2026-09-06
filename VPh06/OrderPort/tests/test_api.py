"""
Тесты API-эндпоинтов приложения.
"""

from fastapi.testclient import TestClient


def test_create_lead_without_auth(client: TestClient):
    payload = {
        "contact_data": {"name": "API Test", "phone": "111"},
        "business_info": "API business",
        "budget": "500",
        "preferred_contact": "email",
        "comments": "test",
        "service_id": None
    }
    response = client.post("/api/v1/leads/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["contact_data"]["name"] == "API Test"


def test_get_leads_requires_auth(client: TestClient):
    response = client.get("/api/v1/leads/")
    assert response.status_code == 401


def test_get_admin_settings_public(client: TestClient):
    # Создаём услугу через авторизованного админа (регистрируемся)
    client.post("/api/auth/register", json={"username": "admin", "password": "pass"})
    login = client.post("/api/auth/login", data={"username": "admin", "password": "pass"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/api/v1/admin-settings/", json={"services": "Test", "budget_range": "100-200"}, headers=headers)

    # Без авторизации список должен быть доступен
    response = client.get("/api/v1/admin-settings/")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_behavior_metrics_requires_auth_for_get(client: TestClient):
    # Создание метрик публично
    lead_resp = client.post("/api/v1/leads/", json={"contact_data": {"name": "Metrics Test"}})
    lead_id = lead_resp.json()["id"]
    metrics_payload = {
        "lead_id": lead_id,
        "page_load_time": 1.23,
        "session_duration": 5.67,
        "clicks": 10,
        "scroll_depth": 50,
        "other_metrics": {"screen": "1920x1080"}
    }
    resp = client.post("/api/v1/behavior-metrics/", json=metrics_payload)
    assert resp.status_code == 200

    # GET должен требовать авторизации
    resp = client.get("/api/v1/behavior-metrics/")
    assert resp.status_code == 401