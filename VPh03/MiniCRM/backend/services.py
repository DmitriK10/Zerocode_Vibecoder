"""
Сервисный слой для управления клиентами, сделками и задачами.
"""
from typing import List, Optional, Dict, Any
from backend.repositories import ClientRepository, DealRepository, TaskRepository
from backend.schemas import ClientCreate, ClientUpdate, DealCreate, TaskCreate
from backend.models import Client, Deal, Task


class ClientService:
    def __init__(self, repo: ClientRepository):
        self.repo = repo

    def create_client(self, data: ClientCreate) -> Client:
        # можно добавить валидацию, например, проверку уникальности email
        return self.repo.create(data)

    def get_clients(self, filters: Optional[Dict[str, Any]] = None) -> List[Client]:
        return self.repo.get_all(filters)

    def get_client(self, client_id: int) -> Optional[Client]:
        return self.repo.get_by_id(client_id)

    def update_client(self, client_id: int, data: ClientUpdate) -> Optional[Client]:
        return self.repo.update(client_id, data.dict(exclude_unset=True))

    def delete_client(self, client_id: int) -> bool:
        return self.repo.delete(client_id)

# Аналогично DealService и TaskService