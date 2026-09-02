from app.services.gpt_proxy_service import GPTProxyService

# Глобальная переменная для хранения клиента (инициализируется в main)
_gpt_client: GPTProxyService = None

def get_gpt_client() -> GPTProxyService:
    """Возвращает единый экземпляр GPT-клиента."""
    if _gpt_client is None:
        raise RuntimeError("GPT client not initialized. Call init_gpt_client() first.")
    return _gpt_client

async def get_gpt_service() -> GPTProxyService:
    """Зависимость для FastAPI – возвращает тот же клиент."""
    return get_gpt_client()