import logging
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lead
from app.schemas import LeadCreate, LeadResponse

logger = logging.getLogger("OrderPort")

class LeadService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_lead(self, lead_data: LeadCreate) -> Lead:
        new_lead = Lead(
            contact_data=lead_data.contact_data,
            business_info=lead_data.business_info,
            business_niche=lead_data.business_niche,
            company_size=lead_data.company_size,
            task_volume=lead_data.task_volume,
            role=lead_data.role,
            budget=lead_data.budget,
            preferred_contact=lead_data.preferred_contact,
            comments=lead_data.comments,
            user_agent=lead_data.user_agent,
            ip_address=lead_data.ip_address,
            referer=lead_data.referer,
            session_id=lead_data.session_id,
            page_load_time=lead_data.page_load_time,
            service_id=lead_data.service_id,
        )
        self.db.add(new_lead)
        await self.db.commit()
        await self.db.refresh(new_lead)
        logger.debug(f"Lead saved to DB with id {new_lead.id}")
        return new_lead

    async def get_lead(self, lead_id: int) -> Optional[LeadResponse]:
        result = await self.db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()
        if not lead:
            return None
        priority = self.compute_priority(lead)
        response = LeadResponse.model_validate(lead)
        response.priority = priority
        logger.debug(f"Retrieved lead {lead_id}")
        return response

    async def get_all_leads(self, skip: int = 0, limit: int = 100, sort_by_priority: bool = False) -> List[LeadResponse]:
        query = select(Lead).offset(skip).limit(limit)
        result = await self.db.execute(query)
        leads = result.scalars().all()
        responses = []
        for lead in leads:
            priority = self.compute_priority(lead)
            response = LeadResponse.model_validate(lead)
            response.priority = priority
            responses.append(response)
        if sort_by_priority:
            responses.sort(key=lambda x: x.priority, reverse=True)
        return responses

    def compute_priority(self, lead: Lead) -> int:
        score = 0
        niche = (lead.business_niche or "").lower()
        if "it" in niche or "интернет" in niche or "digital" in niche:
            score += 20
        elif "производств" in niche or "manufactur" in niche:
            score += 10
        size = (lead.company_size or "").lower()
        if size == "large":
            score += 30
        elif size == "medium":
            score += 20
        elif size == "small":
            score += 10
        volume = (lead.task_volume or "").lower()
        if volume == "high":
            score += 30
        elif volume == "medium":
            score += 20
        elif volume == "low":
            score += 10
        if lead.budget:
            import re
            numbers = re.findall(r'\d+', lead.budget)
            if numbers:
                budget_value = int(numbers[0])
                if budget_value > 1_000_000:
                    score += 20
                elif budget_value > 500_000:
                    score += 15
                elif budget_value > 100_000:
                    score += 10
                else:
                    score += 5
        return min(score, 100)