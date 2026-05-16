# models/table.py
from typing import Optional

class Table:
    """
    Модель столика ресторана.
    """
    def __init__(
        self,
        number: int,
        seats: int,
        location: str = "main hall",
        status: str = "available",
        id: Optional[int] = None
    ):
        self.id = id
        self.number = number
        self.seats = seats
        self.location = location          # 'main hall', 'terrace', 'vip room'
        self.status = status              # 'available', 'occupied', 'maintenance'

    __annotations__ = {
        "id": int,
        "number": int,
        "seats": int,
        "location": str,
        "status": str
    }