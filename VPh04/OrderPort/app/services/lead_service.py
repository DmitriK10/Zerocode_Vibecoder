import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lead
from app.schemas import LeadCreate

logger = logging.getLogger("OrderPort")


class LeadService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_lead(self, lead_data: LeadCreate) -> Lead:
        new_lead = Lead(
            contact_data=lead_data.contact_data,
            business_info=lead_data.business_info,
            budget=lead_data.budget,
            preferred_contact=lead_data.preferred_contact,
            comments=lead_data.comments,
            user_agent=lead_data.user_agent,
            ip_address=lead_data.ip_address,
            referer=lead_data.referer,
            session_id=lead_data.session_id,
            page_load_time=lead_data.page_load_time,
            created_at=datetime.utcnow()
        )
        self.db.add(new_lead)
        await self.db.commit()
        await self.db.refresh(new_lead)
        logger.debug(f"Lead saved to DB with id {new_lead.id}")
        return new_lead

    async def get_lead(self, lead_id: int) -> Lead | None:
        result = await self.db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()
        if lead:
            logger.debug(f"Retrieved lead {lead_id}")
        else:
            logger.debug(f"Lead {lead_id} not found")
        return lead

    async def get_all_leads(self, skip: int = 0, limit: int = 100) -> list[Lead]:
        result = await self.db.execute(select(Lead).offset(skip).limit(limit))
        leads = result.scalars().all()
        logger.debug(f"Retrieved {len(leads)} leads")
        return leads