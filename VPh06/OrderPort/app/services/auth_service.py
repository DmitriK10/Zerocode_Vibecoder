import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models import Admin

logger = logging.getLogger("OrderPort")
# Используем pbkdf2_sha256 – нет ограничения в 72 байта
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[Admin]:
    result = await db.execute(select(Admin).where(Admin.username == username))
    admin = result.scalar_one_or_none()
    if not admin:
        return None
    if not verify_password(password, admin.hashed_password):
        return None
    return admin

async def register_admin(db: AsyncSession, username: str, password: str, email: Optional[str] = None) -> Admin:
    existing = await db.execute(select(Admin).where(Admin.username == username))
    if existing.scalar_one_or_none():
        raise ValueError("Username already registered")
    hashed = get_password_hash(password)
    admin = Admin(username=username, hashed_password=hashed, email=email)
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    logger.info(f"Admin registered: {username}")
    return admin

async def get_admin_by_username(db: AsyncSession, username: str) -> Optional[Admin]:
    result = await db.execute(select(Admin).where(Admin.username == username))
    return result.scalar_one_or_none()

async def get_admin_by_id(db: AsyncSession, admin_id: int) -> Optional[Admin]:
    result = await db.execute(select(Admin).where(Admin.id == admin_id))
    return result.scalar_one_or_none()

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None