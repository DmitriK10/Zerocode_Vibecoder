import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from .config import DB_PATH
from .exceptions import DatabaseError


class DatabaseRepository:
    """Репозиторий для работы с таблицей leads (SQLite)"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Создаёт таблицу leads, если её нет"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS leads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_at TIMESTAMP NOT NULL,
                        name TEXT NOT NULL,
                        contact TEXT NOT NULL,
                        source TEXT NOT NULL,
                        comment TEXT
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Ошибка инициализации БД: {e}")

    def save_lead(self, lead_data: Dict[str, Any]) -> int:
        """
        Сохраняет заявку в БД.
        Возвращает ID вставленной записи.
        """
        try:
            # Используем timezone-aware время (Python 3.11+)
            now_iso = datetime.now(timezone.utc).isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO leads (created_at, name, contact, source, comment)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    now_iso,
                    lead_data["name"],
                    lead_data["contact"],
                    lead_data["source"],
                    lead_data.get("comment", "")
                ))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            raise DatabaseError(f"Ошибка сохранения заявки: {e}")