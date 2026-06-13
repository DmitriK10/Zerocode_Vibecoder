from fastapi import APIRouter
from app.models.response_models import MessageResponse

router = APIRouter(prefix="", tags=["Welcome"])

@router.get("/", response_model=MessageResponse)
async def welcome():
    #return MessageResponse(message="Добро пожаловать в тестовое FastAPI приложение")
    #return MessageResponse(message="Автообновление работает! Версия 2.0")
    return MessageResponse(message="Автообновление работает! Версия 3.0")