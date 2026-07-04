import sqlite3
import logging
from typing import List, Dict
from config import Config

logger = logging.getLogger(__name__)

class Memory:
    """Хранит историю диалогов в SQLite (постоянное хранение)."""

    def __init__(self, db_path: str = Config.DB_PATH, context_limit: int = Config.CONTEXT_LIMIT):
        self.db_path = db_path
        self.context_limit = context_limit
        self._init_db()

    def _init_db(self) -> None:
        """Создаёт таблицу и индексы, если их нет."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        role TEXT,
                        content TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON history(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON history(timestamp)')
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise

    def add_message(self, user_id: int, role: str, content: str) -> None:
        """Добавляет сообщение и удаляет старые записи."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO history (user_id, role, content) VALUES (?, ?, ?)",
                    (user_id, role, content)
                )
                # Удаляем старые записи, оставляя последние context_limit*2
                cursor.execute('''
                    DELETE FROM history
                    WHERE user_id = ? AND id NOT IN (
                        SELECT id FROM history
                        WHERE user_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    )
                ''', (user_id, user_id, self.context_limit * 2))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Ошибка добавления сообщения для user {user_id}: {e}")

    def get_context(self, user_id: int) -> List[Dict[str, str]]:
        """Возвращает последние context_limit сообщений для контекста."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT role, content FROM history
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (user_id, self.context_limit))
                rows = cursor.fetchall()
                # Возвращаем от старых к новым
                return [{"role": row[0], "content": row[1]} for row in reversed(rows)]
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения контекста для user {user_id}: {e}")
            return []

    def clear(self, user_id: int) -> None:
        """Очищает историю пользователя."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Ошибка очистки истории для user {user_id}: {e}")