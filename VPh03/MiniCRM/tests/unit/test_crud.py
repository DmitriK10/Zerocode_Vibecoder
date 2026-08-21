import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import Client
from backend.crud import create_client, get_clients
from backend.schemas import ClientCreate  # <-- добавлен импорт

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_create_client(db_session):
    # Создаём объект ClientCreate, а не словарь
    client_data = ClientCreate(name="John Doe", email="john@example.com", company="Acme")
    client = create_client(db_session, client_data)
    assert client.id is not None
    assert client.name == "John Doe"

def test_get_clients(db_session):
    client_data = ClientCreate(name="Jane", email="jane@example.com")
    create_client(db_session, client_data)
    clients = get_clients(db_session)
    assert len(clients) == 1