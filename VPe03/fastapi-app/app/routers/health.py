from fastapi import APIRouter
from app.models.response_models import MessageResponse

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/", response_model=MessageResponse)
async def health_check():
    return MessageResponse(message="OK")