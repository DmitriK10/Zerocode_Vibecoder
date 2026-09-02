import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import router as v1_router
from app.database import engine
from app.models import Base
from app.services.gpt_proxy_service import GPTProxyService
import os

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("OrderPort")

# Глобальный клиент для GPT
gpt_client = None

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Старт: инициализация БД и GPT-клиента
    await init_db()
    global gpt_client
    gpt_client = GPTProxyService()   # создаём единый экземпляр
    # Сохраняем в модуль зависимостей
    import app.dependencies as deps
    deps._gpt_client = gpt_client
    logger.info("GPT client initialized")
    yield
    # Остановка: закрываем клиент
    if gpt_client:
        await gpt_client.close()
        logger.info("GPT client closed")

app = FastAPI(title="OrderPort API", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    logger.info(f"Static files served from {static_dir}")
else:
    logger.warning(f"Static directory not found: {static_dir}")

@app.get("/health")
async def health():
    return {"status": "ok"}