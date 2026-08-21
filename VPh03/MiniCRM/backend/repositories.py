"""
Репозитории для работы с базой данных (SQLAlchemy).
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.models import Client, Deal, Task
from backend.schemas import ClientCreate, DealCreate, TaskCreate


class ClientRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: ClientCreate) -> Client:
        client = Client(**data.dict())
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        return client

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Client]:
        query = self.db.query(Client)
        if filters:
            if "name" in filters:
                query = query.filter(Client.name.ilike(f"%{filters['name']}%"))
            if "email" in filters:
                query = query.filter(Client.email.ilike(f"%{filters['email']}%"))
            # другие фильтры
        return query.all()

    def get_by_id(self, client_id: int) -> Optional[Client]:
        return self.db.query(Client).filter(Client.id == client_id).first()

    def update(self, client_id: int, data: Dict[str, Any]) -> Optional[Client]:
        client = self.get_by_id(client_id)
        if client:
            for key, value in data.items():
                setattr(client, key, value)
            self.db.commit()
            self.db.refresh(client)
        return client

    def delete(self, client_id: int) -> bool:
        client = self.get_by_id(client_id)
        if client:
            self.db.delete(client)
            self.db.commit()
            return True
        return False


class DealRepository:
    # аналогично
    pass


class TaskRepository:
    # аналогично
    pass