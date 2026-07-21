def test_post_triage_success(client):
    response = client.post(
        "/api/v1/triage",
        json={
            "text": "Не могу войти в аккаунт",
            "channel": "email",
            "client_id": "u1",
        },
    )
    # Подробный вывод при ошибке
    assert response.status_code == 200, (
        f"Ожидался статус 200, получен {response.status_code}. "
        f"Ответ: {response.text}"
    )
    data = response.json()
    assert data["category"] == "billing"
    assert data["escalate"] == False


def test_post_triage_validation_error(client):
    response = client.post(
        "/api/v1/triage",
        json={
            "text": "",   # пустой текст
            "channel": "email",
            "client_id": "u2",
        },
    )
    assert response.status_code == 422, f"Ожидался 422, получен {response.status_code}"