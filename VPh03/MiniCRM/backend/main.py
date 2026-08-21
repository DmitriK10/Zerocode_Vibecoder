"""
backend/main.py
Точка входа FastAPI-приложения с эндпоинтами для клиентов, сделок, задач.
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import engine, get_db, Base
from backend import crud, schemas
from logger import logger

# Создаём таблицы при старте
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mini CRM API", version="1.0.0")


# ---------- Клиенты ----------
@app.get("/clients/", response_model=List[schemas.Client])
def read_clients(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    logger.info("Запрос списка клиентов (skip=%s, limit=%s, search=%s)", skip, limit, search)
    return crud.get_clients(db, skip=skip, limit=limit, search=search)

@app.post("/clients/", response_model=schemas.Client)
def create_client(client: schemas.ClientCreate, db: Session = Depends(get_db)):
    logger.info("Создание клиента: %s", client.name)
    return crud.create_client(db, client)

@app.get("/clients/{client_id}", response_model=schemas.Client)
def read_client(client_id: int, db: Session = Depends(get_db)):
    logger.info("Запрос клиента по ID: %s", client_id)
    db_client = crud.get_client(db, client_id)
    if db_client is None:
        logger.warning("Клиент с ID %s не найден", client_id)
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return db_client

@app.put("/clients/{client_id}", response_model=schemas.Client)
def update_client(client_id: int, client: schemas.ClientUpdate, db: Session = Depends(get_db)):
    logger.info("Обновление клиента с ID %s", client_id)
    db_client = crud.update_client(db, client_id, client)
    if db_client is None:
        logger.warning("Клиент с ID %s не найден для обновления", client_id)
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return db_client

@app.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    logger.info("Удаление клиента с ID %s", client_id)
    if not crud.delete_client(db, client_id):
        logger.warning("Клиент с ID %s не найден для удаления", client_id)
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return {"ok": True}


# ---------- Сделки ----------
@app.get("/deals/", response_model=List[schemas.Deal])
def read_deals(
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    logger.info("Запрос списка сделок (skip=%s, limit=%s, client_id=%s, status=%s)", skip, limit, client_id, status)
    return crud.get_deals(db, skip=skip, limit=limit, client_id=client_id, status=status)

@app.post("/deals/", response_model=schemas.Deal)
def create_deal(deal: schemas.DealCreate, db: Session = Depends(get_db)):
    logger.info("Создание сделки: %s", deal.title)
    return crud.create_deal(db, deal)

@app.get("/deals/{deal_id}", response_model=schemas.Deal)
def read_deal(deal_id: int, db: Session = Depends(get_db)):
    logger.info("Запрос сделки по ID: %s", deal_id)
    db_deal = crud.get_deal(db, deal_id)
    if db_deal is None:
        logger.warning("Сделка с ID %s не найдена", deal_id)
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    return db_deal

@app.put("/deals/{deal_id}", response_model=schemas.Deal)
def update_deal(deal_id: int, deal: schemas.DealUpdate, db: Session = Depends(get_db)):
    logger.info("Обновление сделки с ID %s", deal_id)
    db_deal = crud.update_deal(db, deal_id, deal)
    if db_deal is None:
        logger.warning("Сделка с ID %s не найдена для обновления", deal_id)
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    return db_deal

@app.delete("/deals/{deal_id}")
def delete_deal(deal_id: int, db: Session = Depends(get_db)):
    logger.info("Удаление сделки с ID %s", deal_id)
    if not crud.delete_deal(db, deal_id):
        logger.warning("Сделка с ID %s не найдена для удаления", deal_id)
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    return {"ok": True}


# ---------- Задачи ----------
@app.get("/tasks/", response_model=List[schemas.Task])
def read_tasks(
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[int] = None,
    deal_id: Optional[int] = None,
    is_done: Optional[int] = None,
    db: Session = Depends(get_db)
):
    logger.info("Запрос списка задач (skip=%s, limit=%s, client_id=%s, deal_id=%s, is_done=%s)", skip, limit, client_id, deal_id, is_done)
    return crud.get_tasks(db, skip=skip, limit=limit, client_id=client_id, deal_id=deal_id, is_done=is_done)

@app.post("/tasks/", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    logger.info("Создание задачи: %s", task.title)
    return crud.create_task(db, task)

@app.get("/tasks/{task_id}", response_model=schemas.Task)
def read_task(task_id: int, db: Session = Depends(get_db)):
    logger.info("Запрос задачи по ID: %s", task_id)
    db_task = crud.get_task(db, task_id)
    if db_task is None:
        logger.warning("Задача с ID %s не найдена", task_id)
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return db_task

@app.put("/tasks/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    logger.info("Обновление задачи с ID %s", task_id)
    db_task = crud.update_task(db, task_id, task)
    if db_task is None:
        logger.warning("Задача с ID %s не найдена для обновления", task_id)
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return db_task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    logger.info("Удаление задачи с ID %s", task_id)
    if not crud.delete_task(db, task_id):
        logger.warning("Задача с ID %s не найдена для удаления", task_id)
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return {"ok": True}