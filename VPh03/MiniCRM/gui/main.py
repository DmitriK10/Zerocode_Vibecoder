from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.repositories import ClientRepository, DealRepository, TaskRepository
from backend.services import ClientService, DealService, TaskService
from backend.schemas import ClientCreate, ClientUpdate, DealCreate, TaskCreate

app = FastAPI(title="Mini CRM API")

def get_client_service(db: Session = Depends(get_db)):
    return ClientService(ClientRepository(db))

@app.get("/clients")
def list_clients(service: ClientService = Depends(get_client_service)):
    return service.get_clients()

@app.post("/clients")
def create_client(data: ClientCreate, service: ClientService = Depends(get_client_service)):
    return service.create_client(data)

# остальные эндпоинты аналогично