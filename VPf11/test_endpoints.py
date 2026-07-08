"""
test_endpoints.py
Проверяет работоспособность API, отправляя запросы ко всем ключевым эндпоинтам.
"""
import requests

BASE_URL = "http://localhost:8080"

def test_add_user():
    response = requests.post(f"{BASE_URL}/adduser", json={"name": "testuser"})
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ok"
    assert "id" in data
    assert data["name"] == "testuser"
    return data["id"]

def test_get_user(user_id):
    response = requests.get(f"{BASE_URL}/user/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["name"] == "testuser"

def test_activate_user(user_id):
    response = requests.post(f"{BASE_URL}/activate/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert user_id in data["active"]

def test_slow():
    response = requests.get(f"{BASE_URL}/slow")
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "scheduled"

def test_wrong():
    response = requests.get(f"{BASE_URL}/wrong")
    assert response.status_code == 500
    data = response.json()
    assert data["msg"] == "error"
    assert "division by zero" in data["detail"]

if __name__ == "__main__":
    print("Testing API...")
    user_id = test_add_user()
    test_get_user(user_id)
    test_activate_user(user_id)
    test_slow()
    test_wrong()
    print("All tests passed!")