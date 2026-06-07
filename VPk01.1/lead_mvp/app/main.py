from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

from .models import LeadIn, LeadOut
from .database import DatabaseRepository
from .notifier import FileNotifier
from .service import LeadService
from .exceptions import LeadSaveError

# Настройка логирования для самого FastAPI (отдельно от events.log)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаём зависимости (Dependency Injection)
db_repo = DatabaseRepository()
notifier = FileNotifier()
lead_service = LeadService(db_repo, notifier)

# FastAPI приложение
app = FastAPI(
    title="Lead Intake MVP",
    description="Webhook → SQLite → уведомление (лог-файл)",
    version="1.0.0"
)


@app.post("/lead", response_model=LeadOut, status_code=201)
async def create_lead(lead_in: LeadIn):
    """
    Принимает JSON-заявку, валидирует, сохраняет в SQLite,
    записывает событие в events.log.
    """
    try:
        lead_dict = lead_in.model_dump()
        lead_id = lead_service.process_lead(lead_dict)
        logger.info(f"Lead {lead_id} успешно сохранён и залогирован")
        return LeadOut(id=lead_id)
    except LeadSaveError as e:
        logger.error(f"Ошибка при обработке лида: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Непредвиденная ошибка")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


# Специализированный обработчик для ошибок валидации Pydantic (422 -> 400)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Невалидный запрос. Проверьте поля name, contact (обязательно), source, comment."}
    )

# Обработчик HTTPException удалён – FastAPI обрабатывает их стандартно (JSON с detail)