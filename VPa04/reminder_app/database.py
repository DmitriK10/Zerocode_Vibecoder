import datetime
import sqlite3
from typing import Dict, List, Optional


STATUSES = {"Ожидает", "Готово", "Просрочено", "Отменено"}


class ReminderDatabase:
    def __init__(self, db_path: str = "reminders.db") -> None:
        self.db_path = db_path
        self.initdatabase()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initdatabase(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    due_time TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Ожидает',
                    created_at TEXT NOT NULL,
                    notified INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reminders_due_time ON reminders(due_time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status)")
            conn.commit()

    def add_reminder(self, title: str, description: str, due_time: datetime.datetime) -> int:
        title = title.strip()
        description = description.strip()
        if not title:
            raise ValueError("Заголовок не может быть пустым.")

        now_dt = datetime.datetime.now()
        status = "Просрочено" if due_time < now_dt else "Ожидает"
        due_str = due_time.strftime("%Y-%m-%d %H:%M:%S")
        created_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO reminders (title, description, due_time, status, created_at, notified)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (title, description, due_str, status, created_str),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def get_all_reminders(self, status_filter: Optional[str] = None) -> List[Dict]:
        query = "SELECT * FROM reminders"
        params: tuple = ()

        if status_filter and status_filter != "Все":
            query += " WHERE status = ?"
            params = (status_filter,)

        query += " ORDER BY due_time ASC, id ASC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_due_reminders(self) -> List[Dict]:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM reminders
                WHERE status = 'Ожидает' AND notified = 0 AND due_time <= ?
                ORDER BY due_time ASC, id ASC
                """,
                (now,),
            ).fetchall()
            return [dict(row) for row in rows]

    def sort_by_due_time(self, reminders: List[Dict]) -> List[Dict]:
        return sorted(reminders, key=lambda item: (item["due_time"], item["id"]))

    def update_status(self, reminder_id: int, new_status: str) -> None:
        if new_status not in STATUSES:
            raise ValueError(f"Недопустимый статус: {new_status}")

        notified = 1 if new_status in {"Готово", "Отменено"} else 0
        with self._connect() as conn:
            conn.execute(
                "UPDATE reminders SET status = ?, notified = ? WHERE id = ?",
                (new_status, notified, reminder_id),
            )
            conn.commit()

    def delete_reminder(self, reminder_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
            conn.commit()

    def mark_overdue(self) -> int:
        overdue_dt = datetime.datetime.now() - datetime.timedelta(minutes=1)
        overdue_str = overdue_dt.strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE reminders
                SET status = 'Просрочено', notified = 0
                WHERE status = 'Ожидает' AND due_time <= ?
                """,
                (overdue_str,),
            )
            conn.commit()
            return int(cursor.rowcount)

    def mark_notified(self, reminder_id: int) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE reminders SET notified = 1 WHERE id = ?", (reminder_id,))
            conn.commit()

    def get_reminder_by_id(self, reminder_id: int) -> Optional[Dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,)).fetchone()
            return dict(row) if row else None

    def get_reminders_count(self) -> Dict[str, int]:
        counts: Dict[str, int] = {"Всего": 0, "Ожидает": 0, "Готово": 0, "Просрочено": 0, "Отменено": 0}
        with self._connect() as conn:
            rows = conn.execute("SELECT status, COUNT(*) AS cnt FROM reminders GROUP BY status").fetchall()
            for row in rows:
                status = row["status"]
                cnt = int(row["cnt"])
                if status in counts:
                    counts[status] = cnt
                    counts["Всего"] += cnt
        return counts