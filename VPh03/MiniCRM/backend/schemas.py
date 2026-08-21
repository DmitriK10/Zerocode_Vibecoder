"""
backend/schemas.py
Pydantic-схемы для валидации и сериализации.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ClientBase(BaseModel):
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = "Активен"


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None


class Client(ClientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DealBase(BaseModel):
    title: str
    amount: Optional[float] = None
    status: Optional[str] = "Новая"
    client_id: Optional[int] = None


class DealCreate(DealBase):
    pass


class DealUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    client_id: Optional[int] = None


class Deal(DealBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    is_done: Optional[int] = 0
    client_id: Optional[int] = None
    deal_id: Optional[int] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    is_done: Optional[int] = None
    client_id: Optional[int] = None
    deal_id: Optional[int] = None


class Task(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True