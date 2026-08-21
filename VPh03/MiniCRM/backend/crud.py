"""
backend/crud.py
Функции для взаимодействия с БД.
"""

from sqlalchemy.orm import Session
from backend import models, schemas
from typing import Optional, List


# ---------- Клиенты ----------
def get_client(db: Session, client_id: int):
    return db.query(models.Client).filter(models.Client.id == client_id).first()

def get_clients(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None):
    query = db.query(models.Client)
    if search:
        query = query.filter(
            (models.Client.name.ilike(f"%{search}%")) |
            (models.Client.company.ilike(f"%{search}%")) |
            (models.Client.email.ilike(f"%{search}%"))
        )
    return query.offset(skip).limit(limit).all()

def create_client(db: Session, client: schemas.ClientCreate):
    db_client = models.Client(**client.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def update_client(db: Session, client_id: int, client_update: schemas.ClientUpdate):
    db_client = get_client(db, client_id)
    if not db_client:
        return None
    for key, value in client_update.model_dump(exclude_unset=True).items():
        setattr(db_client, key, value)
    db.commit()
    db.refresh(db_client)
    return db_client

def delete_client(db: Session, client_id: int):
    db_client = get_client(db, client_id)
    if db_client:
        db.delete(db_client)
        db.commit()
        return True
    return False


# ---------- Сделки ----------
def get_deal(db: Session, deal_id: int):
    return db.query(models.Deal).filter(models.Deal.id == deal_id).first()

def get_deals(db: Session, skip: int = 0, limit: int = 100,
              client_id: Optional[int] = None, status: Optional[str] = None):
    query = db.query(models.Deal)
    if client_id is not None:
        query = query.filter(models.Deal.client_id == client_id)
    if status:
        query = query.filter(models.Deal.status == status)
    return query.offset(skip).limit(limit).all()

def create_deal(db: Session, deal: schemas.DealCreate):
    db_deal = models.Deal(**deal.model_dump())
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    return db_deal

def update_deal(db: Session, deal_id: int, deal_update: schemas.DealUpdate):
    db_deal = get_deal(db, deal_id)
    if not db_deal:
        return None
    for key, value in deal_update.model_dump(exclude_unset=True).items():
        setattr(db_deal, key, value)
    db.commit()
    db.refresh(db_deal)
    return db_deal

def delete_deal(db: Session, deal_id: int):
    db_deal = get_deal(db, deal_id)
    if db_deal:
        db.delete(db_deal)
        db.commit()
        return True
    return False


# ---------- Задачи ----------
def get_task(db: Session, task_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def get_tasks(db: Session, skip: int = 0, limit: int = 100,
              client_id: Optional[int] = None, deal_id: Optional[int] = None,
              is_done: Optional[int] = None):
    query = db.query(models.Task)
    if client_id is not None:
        query = query.filter(models.Task.client_id == client_id)
    if deal_id is not None:
        query = query.filter(models.Task.deal_id == deal_id)
    if is_done is not None:
        query = query.filter(models.Task.is_done == is_done)
    return query.offset(skip).limit(limit).all()

def create_task(db: Session, task: schemas.TaskCreate):
    db_task = models.Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, task_id: int, task_update: schemas.TaskUpdate):
    db_task = get_task(db, task_id)
    if not db_task:
        return None
    for key, value in task_update.model_dump(exclude_unset=True).items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int):
    db_task = get_task(db, task_id)
    if db_task:
        db.delete(db_task)
        db.commit()
        return True
    return False