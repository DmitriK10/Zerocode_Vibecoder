import pytest
import json
import os
from appointment_manager import AppointmentManager, APPOINTMENTS_FILE

@pytest.fixture
def clean_manager():
    # Удаляем файл перед каждым тестом
    if os.path.exists(APPOINTMENTS_FILE):
        os.remove(APPOINTMENTS_FILE)
    manager = AppointmentManager()
    yield manager
    # После теста удаляем
    if os.path.exists(APPOINTMENTS_FILE):
        os.remove(APPOINTMENTS_FILE)

@pytest.mark.asyncio
async def test_create_and_get(clean_manager):
    manager = clean_manager
    record = manager.create_appointment(
        user_id=123,
        user_name="Test User",
        topic="Test Topic",
        date_time="2026-08-20 15:00",
        contact="test@mail.com"
    )
    assert record["id"] == 1
    appointments = manager.get_appointments_by_user(123)
    assert len(appointments) == 1
    assert appointments[0]["topic"] == "Test Topic"