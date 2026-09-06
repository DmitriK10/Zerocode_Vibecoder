import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import AdminCreate, AdminLogin, AdminResponse, Token
from app.services.auth_service import (
    authenticate_user,
    register_admin,
    create_access_token,
    get_admin_by_username,
    get_admin_by_id,
)
from app.dependencies import get_current_admin

logger = logging.getLogger("OrderPort")
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def register(admin_data: AdminCreate, db: AsyncSession = Depends(get_db)):
    try:
        admin = await register_admin(
            db,
            username=admin_data.username,
            password=admin_data.password,
            email=admin_data.email
        )
        return admin
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    admin = await authenticate_user(db, form_data.username, form_data.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(admin.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=AdminResponse)
async def read_me(current_admin: AdminResponse = Depends(get_current_admin)):
    return current_admin


@router.get("/check")
async def check_registered(db: AsyncSession = Depends(get_db)):
    admin = await get_admin_by_username(db, "admin")  # Проверяем наличие любого админа
    if admin is None:
        # Проверим, есть ли вообще хоть один админ
        from sqlalchemy import select
        from app.models import Admin
        result = await db.execute(select(Admin))
        any_admin = result.scalars().first()
        if any_admin is None:
            return {"registered": False}
    return {"registered": True}