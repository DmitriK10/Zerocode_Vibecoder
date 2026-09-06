import pytest
from app.services.admin_settings_service import AdminSettingsService
from app.schemas import AdminSettingsCreate


@pytest.mark.asyncio
async def test_create_admin_setting(db_session):
    service = AdminSettingsService(db_session)
    setting_data = AdminSettingsCreate(services="Test", budget_range="100-200")
    setting = await service.create(setting_data)
    assert setting.id is not None
    assert setting.services == "Test"
    assert setting.budget_range == "100-200"


@pytest.mark.asyncio
async def test_get_all_admin_settings(db_session):
    service = AdminSettingsService(db_session)
    await service.create(AdminSettingsCreate(services="A", budget_range="1-2"))
    await service.create(AdminSettingsCreate(services="B", budget_range="3-4"))
    settings = await service.get_all()
    assert len(settings) == 2