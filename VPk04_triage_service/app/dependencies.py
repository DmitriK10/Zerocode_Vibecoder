from app.core.config import settings
from app.llm.proxyapi_client import ProxyAPILLMClient
from app.repository.ticket_repo import TicketRepository
from app.services.rate_limiter import RateLimiter
from app.services.triage_service import TriageService


def get_triage_service() -> TriageService:
    llm_client = ProxyAPILLMClient(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )
    repository = TicketRepository(db_path="tickets.db")
    rate_limiter = RateLimiter(max_requests=settings.RATE_LIMIT_PER_MINUTE)
    return TriageService(
        llm_client=llm_client,
        repository=repository,
        rate_limiter=rate_limiter,
    )