"""
Модуль для работы с базой данных SQLite.
Хранит пользователей, путешествия и расходы.
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any

class Database:
    """Основной класс для взаимодействия с БД (SRP: управление данными)"""
    
    def __init__(self, db_path: str = "travel_bot.db"):
        self.db_path = db_path
        self._init_tables()
    
    def _get_connection(self):
        """Создать и вернуть соединение с БД"""
        return sqlite3.connect(self.db_path)
    
    def _init_tables(self):
        """Инициализация таблиц (вызывается при создании экземпляра)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Таблица пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Таблица путешествий
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT,
                    home_currency TEXT,
                    travel_currency TEXT,
                    exchange_rate REAL,
                    home_balance REAL,
                    travel_balance REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            # Таблица расходов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trip_id INTEGER,
                    amount_travel REAL,
                    amount_home REAL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trip_id) REFERENCES trips (id)
                )
            """)
            # Таблица для хранения активного путешествия пользователя
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS active_trip (
                    user_id INTEGER PRIMARY KEY,
                    trip_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (trip_id) REFERENCES trips (id)
                )
            """)
            conn.commit()
    
    # ---------- Пользователи ----------
    def register_user(self, user_id: int) -> None:
        """Добавить пользователя, если его нет"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            conn.commit()
    
    # ---------- Путешествия ----------
    def create_trip(self, user_id: int, name: str, home_currency: str, travel_currency: str,
                    exchange_rate: float, home_balance: float, travel_balance: float) -> int:
        """Создать новое путешествие, вернуть его ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trips (user_id, name, home_currency, travel_currency, exchange_rate,
                                   home_balance, travel_balance)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, name, home_currency.upper(), travel_currency.upper(),
                  exchange_rate, home_balance, travel_balance))
            conn.commit()
            trip_id = cursor.lastrowid
            # Устанавливаем как активное, если у пользователя нет активного
            cursor.execute("INSERT OR IGNORE INTO active_trip (user_id, trip_id) VALUES (?, ?)", (user_id, trip_id))
            conn.commit()
            return trip_id
    
    def get_user_trips(self, user_id: int) -> List[Dict[str, Any]]:
        """Получить список всех путешествий пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, home_currency, travel_currency, exchange_rate,
                       home_balance, travel_balance, created_at
                FROM trips WHERE user_id = ? ORDER BY created_at DESC
            """, (user_id,))
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0], "name": row[1], "home_currency": row[2],
                    "travel_currency": row[3], "exchange_rate": row[4],
                    "home_balance": row[5], "travel_balance": row[6], "created_at": row[7]
                }
                for row in rows
            ]
    
    def get_trip_by_id(self, trip_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные путешествия по ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trips WHERE id = ?", (trip_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0], "user_id": row[1], "name": row[2],
                    "home_currency": row[3], "travel_currency": row[4],
                    "exchange_rate": row[5], "home_balance": row[6],
                    "travel_balance": row[7], "created_at": row[8]
                }
            return None
    
    def update_balances(self, trip_id: int, new_home_balance: float, new_travel_balance: float) -> None:
        """Обновить балансы путешествия"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE trips SET home_balance = ?, travel_balance = ? WHERE id = ?
            """, (new_home_balance, new_travel_balance, trip_id))
            conn.commit()
    
    def update_exchange_rate(self, trip_id: int, new_rate: float) -> None:
        """Обновить курс обмена для путешествия"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE trips SET exchange_rate = ? WHERE id = ?", (new_rate, trip_id))
            conn.commit()
    
    # ---------- Активное путешествие ----------
    def get_active_trip(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить активное путешествие пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT trip_id FROM active_trip WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row and row[0]:
                return self.get_trip_by_id(row[0])
            return None
    
    def set_active_trip(self, user_id: int, trip_id: int) -> None:
        """Установить активное путешествие"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO active_trip (user_id, trip_id) VALUES (?, ?)
            """, (user_id, trip_id))
            conn.commit()
    
    # ---------- Расходы ----------
    def add_expense(self, trip_id: int, amount_travel: float, amount_home: float, description: str = "") -> None:
        """Добавить запись о расходе"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO expenses (trip_id, amount_travel, amount_home, description)
                VALUES (?, ?, ?, ?)
            """, (trip_id, amount_travel, amount_home, description))
            conn.commit()
    
    def get_expenses(self, trip_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Получить последние расходы для путешествия"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT amount_travel, amount_home, description, created_at
                FROM expenses WHERE trip_id = ? ORDER BY created_at DESC LIMIT ?
            """, (trip_id, limit))
            rows = cursor.fetchall()
            return [
                {
                    "amount_travel": row[0], "amount_home": row[1],
                    "description": row[2], "created_at": row[3]
                }
                for row in rows
            ]