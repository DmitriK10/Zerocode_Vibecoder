import logging
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AdminSettings
from app.schemas import AdminSettingsCreate

logger = logging.getLogger("OrderPort")

class AdminSettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: AdminSettingsCreate) -> AdminSettings:
        new_setting = AdminSettings(
            services=data.services,
            budget_range=data.budget_range
        )
        self.db.add(new_setting)
        await self.db.commit()
        await self.db.refresh(new_setting)
        return new_setting

    async def get_all(self) -> List[AdminSettings]:
        result = await self.db.execute(select(AdminSettings).order_by(AdminSettings.id))
        return result.scalars().all()

    async def get_by_id(self, setting_id: int) -> Optional[AdminSettings]:
        result = await self.db.execute(select(AdminSettings).where(AdminSettings.id == setting_id))
        return result.scalar_one_or_none()

    async def update(self, setting_id: int, data: AdminSettingsCreate) -> Optional[AdminSettings]:
        setting = await self.get_by_id(setting_id)
        if not setting:
            return None
        setting.services = data.services
        setting.budget_range = data.budget_range
        await self.db.commit()
        await self.db.refresh(setting)
        return setting

    async def delete(self, setting_id: int) -> bool:
        setting = await self.get_by_id(setting_id)
        if not setting:
            return False
        await self.db.delete(setting)
        await self.db.commit()
        return True