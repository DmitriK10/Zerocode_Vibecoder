import logging
import traceback
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import LeadCreate, LeadResponse
from app.services.lead_service import LeadService
from app.services.gpt_proxy_service import GPTProxyService
from app.dependencies import get_gpt_service

logger = logging.getLogger("OrderPort")
router = APIRouter(prefix="/api/v1", tags=["leads"])


@router.post("/leads/", response_model=LeadResponse)
async def create_lead(
    lead: LeadCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    if not lead.ip_address:
        lead.ip_address = request.client.host

    logger.info(f"Received lead data: {lead.dict()}")
    service = LeadService(db)
    try:
        new_lead = await service.create_lead(lead)
        logger.info(f"Lead created with id {new_lead.id}")
        return new_lead
    except Exception as e:
        error_text = traceback.format_exc()
        logger.error(f"Error creating lead: {str(e)}\n{error_text}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/leads/", response_model=List[LeadResponse])
async def get_leads(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Fetching leads: skip={skip}, limit={limit}")
    service = LeadService(db)
    leads = await service.get_all_leads(skip, limit)
    return leads


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Fetching lead with id {lead_id}")
    service = LeadService(db)
    lead = await service.get_lead(lead_id)
    if not lead:
        logger.warning(f"Lead {lead_id} not found")
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("/leads/{lead_id}/analyze")
async def analyze_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    gpt: GPTProxyService = Depends(get_gpt_service)
):
    logger.info(f"Analyzing lead {lead_id} with GPT")
    service = LeadService(db)
    lead = await service.get_lead(lead_id)
    if not lead:
        logger.warning(f"Lead {lead_id} not found for analysis")
        raise HTTPException(status_code=404, detail="Lead not found")

    prompt = (
        f"Проанализируй следующую заявку от клиента:\n"
        f"Контактные данные: {lead.contact_data}\n"
        f"Информация о бизнесе: {lead.business_info}\n"
        f"Бюджет: {lead.budget}\n"
        f"Комментарии: {lead.comments}\n"
        f"Дай краткую рекомендацию по обработке этой заявки."
    )
    try:
        analysis = await gpt.generate_response(prompt)
        logger.info(f"Analysis completed for lead {lead_id}")
        return {"lead_id": lead_id, "analysis": analysis}
    except Exception as e:
        logger.error(f"GPT analysis failed for lead {lead_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))