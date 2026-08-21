import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import Client
from backend.repositories import ClientRepository
from backend.schemas import ClientCreate

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_create_client(db_session):
    repo = ClientRepository(db_session)
    data = ClientCreate(name="Test", email="test@example.com")
    client = repo.create(data)
    assert client.id is not None
    assert client.name == "Test"