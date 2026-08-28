from app.services.gpt_proxy_service import GPTProxyService

async def get_gpt_service() -> GPTProxyService:
    service = GPTProxyService()
    try:
        yield service
    finally:
        await service.close()