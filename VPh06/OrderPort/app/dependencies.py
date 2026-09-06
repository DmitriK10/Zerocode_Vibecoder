from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.gpt_proxy_service import GPTProxyService
from app.database import get_db
from app.services.auth_service import decode_token, get_admin_by_id

# Глобальная переменная для хранения клиента (инициализируется в main)
_gpt_client: GPTProxyService = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_gpt_client() -> GPTProxyService:
    """Возвращает единый экземпляр GPT-клиента."""
    if _gpt_client is None:
        raise RuntimeError("GPT client not initialized. Call init_gpt_client() first.")
    return _gpt_client

async def get_gpt_service() -> GPTProxyService:
    """Зависимость для FastAPI – возвращает тот же клиент."""
    return get_gpt_client()

async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    admin_id = payload.get("sub")
    if admin_id is None:
        raise credentials_exception
    admin = await get_admin_by_id(db, int(admin_id))
    if admin is None:
        raise credentials_exception
    return admin