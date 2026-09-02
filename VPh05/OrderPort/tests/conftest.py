import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app import main
from app.main import app
from app.database import get_db
from app.models import Base

# Тестовая БД – SQLite
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
test_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# Подменяем движок в модуле main (именно его использует main.py)
main.engine = test_engine

TestingSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client