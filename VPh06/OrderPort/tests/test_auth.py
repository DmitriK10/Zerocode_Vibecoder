import pytest
from fastapi.testclient import TestClient


def test_register_and_login(client: TestClient):
    resp = client.post("/api/auth/register", json={
        "username": "admin",
        "password": "secret123",
        "email": "admin@example.com"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "admin"
    assert data["id"] is not None

    resp = client.post("/api/auth/login", data={"username": "admin", "password": "secret123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"


def test_register_duplicate_username(client: TestClient):
    client.post("/api/auth/register", json={"username": "admin2", "password": "pass123"})
    resp = client.post("/api/auth/register", json={"username": "admin2", "password": "pass456"})
    assert resp.status_code == 400
    assert "already" in resp.json()["detail"]


def test_login_wrong_password(client: TestClient):
    client.post("/api/auth/register", json={"username": "admin3", "password": "pass123"})
    resp = client.post("/api/auth/login", data={"username": "admin3", "password": "wrong"})
    assert resp.status_code == 401