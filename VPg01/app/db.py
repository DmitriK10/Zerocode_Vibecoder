import sqlite3
import logging
from typing import List

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_theses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    thesis TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        logger.info("База данных инициализирована: %s", self.db_path)

    def save_thesis(self, user_id: int, thesis: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_theses (user_id, thesis) VALUES (?, ?)",
                (user_id, thesis)
            )
            conn.commit()
        logger.debug("Сохранён тезис для user_id=%d: %s", user_id, thesis)

    def get_theses(self, user_id: int) -> List[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT thesis FROM user_theses WHERE user_id = ? ORDER BY created_at",
                (user_id,)
            )
            rows = cursor.fetchall()
        return [row[0] for row in rows]

    def clear_theses(self, user_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_theses WHERE user_id = ?", (user_id,))
            conn.commit()
        logger.info("Тезисы очищены для user_id=%d", user_id)