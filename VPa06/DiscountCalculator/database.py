"""
Реализация репозитория на базе SQLite.
"""

import sqlite3
from typing import List
from interfaces import ICalculationRepository
from models import CalculationResult, CalculationInput
from datetime import datetime


class SQLiteCalculationRepository(ICalculationRepository):
    """
    Хранилище истории расчётов в SQLite.
    При инициализации автоматически создаёт таблицу, если её нет.
    """

    def __init__(self, db_path: str = "calculations.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Создать таблицу calculations, если она не существует."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_price REAL NOT NULL,
                    discount_percent INTEGER NOT NULL,
                    fixed_discount REAL NOT NULL,
                    final_price REAL NOT NULL,
                    timestamp DATETIME NOT NULL
                )
            """)
            conn.commit()

    def save(self, result: CalculationResult) -> None:
        """Сохранить результат в БД."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO calculations 
                (original_price, discount_percent, fixed_discount, final_price, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                result.original_price,
                result.discount_percent,
                result.fixed_discount,
                result.final_price,
                result.timestamp.isoformat()
            ))
            conn.commit()

    def get_all(self) -> List[CalculationResult]:
        """Получить все записи из истории, отсортированные по времени (новые сначала)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT original_price, discount_percent, fixed_discount, final_price, timestamp
                FROM calculations
                ORDER BY timestamp DESC
            """)
            rows = cursor.fetchall()

        results = []
        for row in rows:
            orig_price, disc_percent, fixed_disc, final_price, ts_str = row
            input_data = CalculationInput(
                original_price=orig_price,
                discount_percent=disc_percent,
                fixed_discount=fixed_disc
            )
            results.append(CalculationResult(
                **input_data.__dict__,
                final_price=final_price,
                timestamp=datetime.fromisoformat(ts_str)
            ))
        return results