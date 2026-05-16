# models/booking.py
from datetime import datetime
from typing import Optional

class Booking:
    """
    Модель бронирования столика.
    """
    def __init__(
        self,
        user_id: int,
        table_id: int,
        booking_date: datetime,
        start_time: datetime,
        end_time: datetime,
        guests_count: int,
        status: str = "confirmed",
        id: Optional[int] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.user_id = user_id
        self.table_id = table_id
        self.booking_date = booking_date   # дата бронирования (может совпадать с start_time)
        self.start_time = start_time
        self.end_time = end_time
        self.guests_count = guests_count
        self.status = status               # 'confirmed', 'cancelled', 'completed'
        self.created_at = created_at or datetime.now()

    # Внешние ключи для автоматического создания связей
    __foreign_keys__ = [
        {"column": "user_id", "ref_table": "users", "ref_column": "id"},
        {"column": "table_id", "ref_table": "tables", "ref_column": "id"}
    ]

    __annotations__ = {
        "id": int,
        "user_id": int,
        "table_id": int,
        "booking_date": datetime,
        "start_time": datetime,
        "end_time": datetime,
        "guests_count": int,
        "status": str,
        "created_at": datetime
    }