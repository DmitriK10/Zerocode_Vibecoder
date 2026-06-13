from fastapi import APIRouter, Depends
from app.services.datetime_service import DateTimeService, SystemDateTimeService
from app.models.response_models import DateTimeResponse

router = APIRouter(prefix="/datetime", tags=["DateTime"])

def get_datetime_service() -> DateTimeService:
    provider = SystemDateTimeService()
    return DateTimeService(provider)

@router.get("/current", response_model=DateTimeResponse)
async def get_current_datetime(
    service: DateTimeService = Depends(get_datetime_service)
):
    info = service.get_current_datetime_info()
    return DateTimeResponse(**info)