# models/user.py
from datetime import datetime
from typing import Optional

class User:
    """
    Модель пользователя системы бронирования.
    """
    def __init__(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        role: str = "user",
        status: str = "active",
        id: Optional[int] = None,
        registered_at: Optional[datetime] = None
    ):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password          # В учебном проекте – открытый пароль
        self.role = role                  # 'user' или 'admin'
        self.status = status              # 'active' или 'blocked'
        self.registered_at = registered_at or datetime.now()

    # Аннотации для автоматического создания таблицы
    __annotations__ = {
        "id": int,
        "first_name": str,
        "last_name": str,
        "email": str,
        "password": str,
        "role": str,
        "status": str,
        "registered_at": datetime
    }