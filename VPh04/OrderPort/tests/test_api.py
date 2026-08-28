"""
Тесты API-эндпоинтов приложения.

Проверяют корректность работы HTTP-запросов к /api/v1/leads/:
- создание заявки (POST)
- получение списка (GET)
- обработку несуществующего ID (404)
"""

from fastapi.testclient import TestClient


def test_create_lead(client: TestClient):
    """
    Проверяет создание новой заявки через POST /api/v1/leads/.

    Ожидается:
    - статус-код 200
    - в ответе присутствует поле id
    - контактные данные совпадают с отправленными
    """
    payload = {
        "contact_data": {"name": "API Test", "phone": "111"},
        "business_info": "API business",
        "budget": "500",
        "preferred_contact": "email",
        "comments": "test"
    }
    response = client.post("/api/v1/leads/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["contact_data"]["name"] == "API Test"


def test_get_leads(client: TestClient):
    """
    Проверяет получение списка заявок через GET /api/v1/leads/.

    Предварительно создаются две заявки, затем запрашивается список.
    Ожидается:
    - статус-код 200
    - в ответе массив, содержащий как минимум 2 записи
    """
    for i in range(2):
        client.post("/api/v1/leads/", json={"contact_data": {"name": f"Lead{i}"}})
    response = client.get("/api/v1/leads/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_get_lead_not_found(client: TestClient):
    """
    Проверяет поведение при запросе несуществующей заявки.

    Ожидается:
    - статус-код 404 (Not Found)
    """
    response = client.get("/api/v1/leads/9999")
    assert response.status_code == 404