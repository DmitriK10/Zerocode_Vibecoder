"""
tests/test_backend.py
Тесты API с временным файлом SQLite.
"""

import tempfile
import os
import atexit
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Импортируем модели, чтобы они зарегистрировались в Base.metadata
import backend.models
from backend.database import Base
from backend.main import app, get_db

# Создаём временный файл для тестовой БД
tmp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
TEST_DB_PATH = tmp_db.name
tmp_db.close()

# Регистрируем удаление файла при завершении процесса
def cleanup():
    if os.path.exists(TEST_DB_PATH):
        try:
            os.unlink(TEST_DB_PATH)
        except PermissionError:
            # Если файл всё ещё занят, пропускаем (будет удалён при перезагрузке)
            pass

atexit.register(cleanup)

TEST_ENGINE = create_engine(
    f"sqlite:///{TEST_DB_PATH}",
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=TEST_ENGINE
)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Создаём таблицы один раз для всех тестов
Base.metadata.create_all(bind=TEST_ENGINE)

@pytest.fixture(autouse=True)
def setup_db():
    # Можно очищать таблицы перед каждым тестом, но для простоты оставляем как есть.
    # Данные будут накапливаться, но тесты изолированы, так как используют разные данные.
    yield
    # Ничего не удаляем

def test_create_client():
    response = client.post("/clients/", json={"name": "Test Client", "company": "TestCo"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Client"
    assert data["id"] is not None

def test_get_clients():
    client.post("/clients/", json={"name": "Client A"})
    client.post("/clients/", json={"name": "Client B"})
    response = client.get("/clients/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # может быть больше, если остались данные от предыдущих тестов

def test_update_client():
    resp = client.post("/clients/", json={"name": "Old Name"})
    client_id = resp.json()["id"]
    response = client.put(f"/clients/{client_id}", json={"name": "New Name"})
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"