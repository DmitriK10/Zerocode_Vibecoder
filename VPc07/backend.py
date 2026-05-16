# backend.py
from typing import List, Dict, Any, Optional
from datetime import datetime
from database_driver import DatabaseDriver
from models.user import User
from models.table import Table
from models.booking import Booking

# ---------- USERS ----------
def create_user(db: DatabaseDriver, user: User) -> int:
    data = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "password": user.password,
        "role": user.role,
        "status": user.status,
        "registered_at": user.registered_at or datetime.now()
    }
    return db.insert("users", data)

def get_all_users(db: DatabaseDriver) -> List[Dict[str, Any]]:
    return db.select("SELECT * FROM users ORDER BY id")

def get_user_by_id(db: DatabaseDriver, user_id: int) -> Optional[Dict[str, Any]]:
    results = db.select("SELECT * FROM users WHERE id = %s", (user_id,))
    return results[0] if results else None

def update_user(db: DatabaseDriver, user_id: int, updated_data: Dict[str, Any]) -> None:
    db.update("users", updated_data, "id = %s", (user_id,))

def delete_user(db: DatabaseDriver, user_id: int) -> None:
    db.delete("users", "id = %s", (user_id,))

# ---------- TABLES ----------
def create_table(db: DatabaseDriver, table: Table) -> int:
    data = {
        "number": table.number,
        "seats": table.seats,
        "location": table.location,
        "status": table.status
    }
    return db.insert("tables", data)

def get_all_tables(db: DatabaseDriver) -> List[Dict[str, Any]]:
    return db.select("SELECT * FROM tables ORDER BY id")

def get_table_by_id(db: DatabaseDriver, table_id: int) -> Optional[Dict[str, Any]]:
    results = db.select("SELECT * FROM tables WHERE id = %s", (table_id,))
    return results[0] if results else None

def update_table(db: DatabaseDriver, table_id: int, updated_data: Dict[str, Any]) -> None:
    db.update("tables", updated_data, "id = %s", (table_id,))

def delete_table(db: DatabaseDriver, table_id: int) -> None:
    db.delete("tables", "id = %s", (table_id,))

# ---------- BOOKINGS ----------
def create_booking(db: DatabaseDriver, booking: Booking) -> int:
    data = {
        "user_id": booking.user_id,
        "table_id": booking.table_id,
        "booking_date": booking.booking_date,
        "start_time": booking.start_time,
        "end_time": booking.end_time,
        "guests_count": booking.guests_count,
        "status": booking.status,
        "created_at": booking.created_at or datetime.now()
    }
    return db.insert("bookings", data)

def get_all_bookings(db: DatabaseDriver) -> List[Dict[str, Any]]:
    return db.select("SELECT * FROM bookings ORDER BY id")

def get_booking_by_id(db: DatabaseDriver, booking_id: int) -> Optional[Dict[str, Any]]:
    results = db.select("SELECT * FROM bookings WHERE id = %s", (booking_id,))
    return results[0] if results else None

def update_booking(db: DatabaseDriver, booking_id: int, updated_data: Dict[str, Any]) -> None:
    db.update("bookings", updated_data, "id = %s", (booking_id,))

def delete_booking(db: DatabaseDriver, booking_id: int) -> None:
    db.delete("bookings", "id = %s", (booking_id,))

# ---------- BUSINESS LOGIC ----------
def check_table_availability(db: DatabaseDriver, table_id: int,
                             start_time: datetime, end_time: datetime) -> bool:
    """
    Проверяет, свободен ли столик в заданном временном интервале.
    """
    query = """
        SELECT COUNT(*) AS cnt FROM bookings
        WHERE table_id = %s
          AND status = 'confirmed'
          AND start_time < %s
          AND end_time > %s
    """
    result = db.select(query, (table_id, end_time, start_time))
    return result[0]["cnt"] == 0

# Вспомогательные функции для GUI (возвращают словари id->name)
def get_users_choices(db: DatabaseDriver) -> Dict[int, str]:
    users = get_all_users(db)
    return {u["id"]: f"{u['first_name']} {u['last_name']} ({u['email']})" for u in users}

def get_tables_choices(db: DatabaseDriver) -> Dict[int, str]:
    tables = get_all_tables(db)
    return {t["id"]: f"Стол №{t['number']} (мест: {t['seats']})" for t in tables}