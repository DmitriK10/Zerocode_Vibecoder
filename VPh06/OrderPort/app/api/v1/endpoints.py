import logging
import traceback
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    LeadCreate, LeadResponse,
    AdminSettingsCreate, AdminSettingsResponse,
    BehaviorMetricsCreate, BehaviorMetricsResponse,
    AnalysisResponse
)
from app.services.lead_service import LeadService
from app.services.admin_settings_service import AdminSettingsService
from app.services.behavior_metrics_service import BehaviorMetricsService
from app.services.gpt_proxy_service import GPTProxyService
from app.dependencies import get_gpt_service, get_current_admin

logger = logging.getLogger("OrderPort")
router = APIRouter(prefix="/api/v1", tags=["leads"])

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

# ---------- Lead endpoints ----------
@router.post("/leads/", response_model=LeadResponse)
async def create_lead(
    lead: LeadCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    if not lead.ip_address:
        lead.ip_address = get_client_ip(request)

    logger.info("Received lead data")
    service = LeadService(db)
    try:
        new_lead = await service.create_lead(lead)
        logger.info(f"Lead created with id {new_lead.id}")
        return new_lead
    except Exception as e:
        error_text = traceback.format_exc()
        logger.error(f"Error creating lead: {str(e)}\n{error_text}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/leads/", response_model=List[LeadResponse])
async def get_leads(
    skip: int = 0,
    limit: int = 100,
    sort_by_priority: bool = Query(False, description="Сортировать по приоритету"),
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    logger.info(f"Fetching leads: skip={skip}, limit={limit}, sort_by_priority={sort_by_priority}")
    service = LeadService(db)
    leads = await service.get_all_leads(skip, limit, sort_by_priority=sort_by_priority)
    return leads

@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db), admin = Depends(get_current_admin)):
    logger.info(f"Fetching lead with id {lead_id}")
    service = LeadService(db)
    lead = await service.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.post("/leads/{lead_id}/analyze", response_model=AnalysisResponse)
async def analyze_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    gpt: GPTProxyService = Depends(get_gpt_service),
    admin = Depends(get_current_admin)
):
    logger.info(f"Analyzing lead {lead_id} with GPT")
    service = LeadService(db)
    lead = await service.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    prompt = (
        f"Проанализируй следующую заявку от клиента:\n"
        f"Контактные данные: {lead.contact_data}\n"
        f"Информация о бизнесе: {lead.business_info}\n"
        f"Ниша: {lead.business_niche}\n"
        f"Размер компании: {lead.company_size}\n"
        f"Объём задачи: {lead.task_volume}\n"
        f"Роль: {lead.role}\n"
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

# ---------- AdminSettings endpoints ----------
@router.post("/admin-settings/", response_model=AdminSettingsResponse)
async def create_admin_setting(
    setting: AdminSettingsCreate,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    service = AdminSettingsService(db)
    try:
        new_setting = await service.create(setting)
        return new_setting
    except Exception as e:
        logger.error(f"Error creating admin setting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin-settings/", response_model=List[AdminSettingsResponse])
async def get_admin_settings(db: AsyncSession = Depends(get_db)):
    service = AdminSettingsService(db)
    settings = await service.get_all()
    return settings

@router.get("/admin-settings/{setting_id}", response_model=AdminSettingsResponse)
async def get_admin_setting(setting_id: int, db: AsyncSession = Depends(get_db), admin = Depends(get_current_admin)):
    service = AdminSettingsService(db)
    setting = await service.get_by_id(setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting

@router.put("/admin-settings/{setting_id}", response_model=AdminSettingsResponse)
async def update_admin_setting(
    setting_id: int,
    setting: AdminSettingsCreate,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    service = AdminSettingsService(db)
    updated = await service.update(setting_id, setting)
    if not updated:
        raise HTTPException(status_code=404, detail="Setting not found")
    return updated

@router.delete("/admin-settings/{setting_id}")
async def delete_admin_setting(setting_id: int, db: AsyncSession = Depends(get_db), admin = Depends(get_current_admin)):
    service = AdminSettingsService(db)
    deleted = await service.delete(setting_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Setting not found")
    return {"ok": True}

# ---------- BehaviorMetrics endpoints ----------
@router.post("/behavior-metrics/", response_model=BehaviorMetricsResponse)
async def create_behavior_metrics(
    metrics: BehaviorMetricsCreate,
    db: AsyncSession = Depends(get_db)
):
    service = BehaviorMetricsService(db)
    try:
        new_metrics = await service.create(metrics)
        return new_metrics
    except Exception as e:
        logger.error(f"Error creating behavior metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/behavior-metrics/", response_model=List[BehaviorMetricsResponse])
async def get_all_behavior_metrics(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    service = BehaviorMetricsService(db)
    return await service.get_all(skip=skip, limit=limit)

@router.get("/behavior-metrics/by-lead/{lead_id}", response_model=BehaviorMetricsResponse)
async def get_behavior_metrics_by_lead(lead_id: int, db: AsyncSession = Depends(get_db), admin = Depends(get_current_admin)):
    service = BehaviorMetricsService(db)
    metrics = await service.get_by_lead_id(lead_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Metrics not found")
    return metrics