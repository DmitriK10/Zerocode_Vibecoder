import logging
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BehaviorMetrics
from app.schemas import BehaviorMetricsCreate

logger = logging.getLogger("OrderPort")

class BehaviorMetricsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: BehaviorMetricsCreate) -> BehaviorMetrics:
        metrics = BehaviorMetrics(
            lead_id=data.lead_id,
            page_load_time=data.page_load_time,
            session_duration=data.session_duration,
            clicks=data.clicks,
            scroll_depth=data.scroll_depth,
            other_metrics=data.other_metrics
        )
        self.db.add(metrics)
        await self.db.commit()
        await self.db.refresh(metrics)
        logger.debug(f"BehaviorMetrics created for lead {data.lead_id}")
        return metrics

    async def get_by_lead_id(self, lead_id: int) -> Optional[BehaviorMetrics]:
        result = await self.db.execute(select(BehaviorMetrics).where(BehaviorMetrics.lead_id == lead_id))
        return result.scalar_one_or_none()

    async def get_all(self) -> List[BehaviorMetrics]:
        result = await self.db.execute(select(BehaviorMetrics).order_by(BehaviorMetrics.id))
        return result.scalars().all()