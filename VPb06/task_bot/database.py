import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional
import os
from config import DATABASE_PATH

class TaskRepository:
    """Репозиторий для работы с таблицей tasks (соблюдение Dependency Inversion)"""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Создание таблицы и добавление новых столбцов, если их нет (миграция)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Создаём таблицу, если её ещё нет
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            # Добавляем колонку status, если отсутствует
            try:
                cursor.execute("ALTER TABLE tasks ADD COLUMN status TEXT DEFAULT 'Новая'")
            except sqlite3.OperationalError:
                pass  # колонка уже существует
            # Добавляем колонку category, если отсутствует
            try:
                cursor.execute("ALTER TABLE tasks ADD COLUMN category TEXT DEFAULT 'Общая'")
            except sqlite3.OperationalError:
                pass
            conn.commit()

    def add_task(self, text: str, user_id: int, status: str = "Новая", category: str = "Общая") -> None:
        """Добавление новой задачи с указанием статуса и категории"""
        created_at = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (text, user_id, created_at, status, category) VALUES (?, ?, ?, ?, ?)",
                (text, user_id, created_at, status, category)
            )
            conn.commit()

    def get_user_tasks(self, user_id: int) -> List[Tuple[int, str, str, str, str]]:
        """Получение всех задач пользователя (id, text, created_at, status, category)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, text, created_at, status, category FROM tasks WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            return cursor.fetchall()

    def get_all_tasks(self) -> List[Tuple[int, str, int, str, str, str]]:
        """Получение всех задач для CSV (id, text, user_id, created_at, status, category)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, text, user_id, created_at, status, category FROM tasks ORDER BY created_at DESC")
            return cursor.fetchall()