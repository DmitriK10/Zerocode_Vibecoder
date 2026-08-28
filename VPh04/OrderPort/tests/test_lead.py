"""
Тесты бизнес-логики работы с заявками (LeadService).

Проверяют CRUD-операции:
- создание заявки
- получение по ID
- получение списка с пагинацией
"""

import pytest
from app.services.lead_service import LeadService
from app.schemas import LeadCreate


@pytest.mark.asyncio
async def test_create_lead(db_session):
    """
    Проверяет создание заявки через LeadService.

    Ожидается:
    - созданная заявка имеет непустой id
    - contact_data содержит переданные данные
    """
    service = LeadService(db_session)
    lead_data = LeadCreate(
        contact_data={"name": "Test", "phone": "123"},
        business_info="Test business",
        budget="1000",
        preferred_contact="phone",
        comments="test comment"
    )
    lead = await service.create_lead(lead_data)
    assert lead.id is not None
    assert lead.contact_data["name"] == "Test"


@pytest.mark.asyncio
async def test_get_lead(db_session):
    """
    Проверяет получение заявки по её ID.

    Создаётся заявка, затем запрашивается по ID.
    Ожидается:
    - полученная заявка не None
    - id и contact_data совпадают с созданными
    """
    service = LeadService(db_session)
    lead_data = LeadCreate(
        contact_data={"name": "Test2", "phone": "456"},
        business_info="Test business 2"
    )
    created = await service.create_lead(lead_data)
    fetched = await service.get_lead(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.contact_data["name"] == "Test2"


@pytest.mark.asyncio
async def test_get_all_leads(db_session):
    """
    Проверяет получение списка заявок с пагинацией.

    Создаются три заявки, затем запрашивается список (skip=0, limit=10).
    Ожидается:
    - длина списка равна 3
    """
    service = LeadService(db_session)
    for i in range(3):
        lead_data = LeadCreate(contact_data={"name": f"User{i}"})
        await service.create_lead(lead_data)
    leads = await service.get_all_leads(skip=0, limit=10)
    assert len(leads) == 3