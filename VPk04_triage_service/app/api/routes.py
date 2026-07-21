import logging
from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import TriageRequest, TriageResponse
from app.services.triage_service import TriageService
from app.dependencies import get_triage_service
from app.core.exceptions import RateLimitExceededError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/triage", response_model=TriageResponse)
async def triage(
    request: TriageRequest,
    service: TriageService = Depends(get_triage_service),
):
    try:
        return await service.process(request)
    except RateLimitExceededError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.exception("Ошибка при обработке запроса")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")