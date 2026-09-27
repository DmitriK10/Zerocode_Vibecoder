from app.llm.base import LLMClient
from app.repository.ticket_repo import TicketRepository
from app.services.rate_limiter import RateLimiter
from app.models.schemas import TriageRequest, TriageResponse
from app.core.exceptions import LLMServiceError, RateLimitExceededError
import logging

logger = logging.getLogger(__name__)


class TriageService:
    def __init__(
        self,
        llm_client: LLMClient,
        repository: TicketRepository,
        rate_limiter: RateLimiter,
    ):
        self.llm_client = llm_client
        self.repository = repository
        self.rate_limiter = rate_limiter

    async def process(self, request: TriageRequest) -> TriageResponse:
        # 1. Проверка лимита
        if not self.rate_limiter.is_allowed(request.client_id):
            raise RateLimitExceededError("Превышен лимит запросов")

        # 2. Попытка обработки LLM
        try:
            result = await self.llm_client.triage(request.text)
            category = result["category"]
            draft_reply = result["draft_reply"]
            confidence = result["confidence"]
            escalate = result["escalate"]
            error = None
        except LLMServiceError as e:
            logger.warning(f"LLM error: {e}")
            category = "other"
            draft_reply = "передано оператору"
            confidence = "low"
            escalate = True
            error = str(e)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            category = "other"
            draft_reply = "передано оператору"
            confidence = "low"
            escalate = True
            error = f"Непредвиденная ошибка: {str(e)}"

        # 3. Сохранение в БД
        self.repository.save_ticket(
            client_id=request.client_id,
            channel=request.channel,
            text=request.text,
            category=category,
            confidence=confidence,
            escalate=escalate,
            draft_reply=draft_reply,
            error=error,
        )

        # 4. Ответ
        return TriageResponse(
            category=category,
            draft_reply=draft_reply,
            confidence=confidence,
            escalate=escalate,
        )