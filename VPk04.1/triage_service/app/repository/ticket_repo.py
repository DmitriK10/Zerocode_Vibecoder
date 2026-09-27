import sqlite3
import datetime
from typing import Optional


class TicketRepository:
    def __init__(self, db_path: str = "tickets.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    text TEXT NOT NULL,
                    category TEXT,
                    confidence TEXT,
                    escalate INTEGER,
                    draft_reply TEXT,
                    error TEXT
                )
            """)
            conn.commit()

    def save_ticket(
        self,
        client_id: str,
        channel: str,
        text: str,
        category: Optional[str] = None,
        confidence: Optional[str] = None,
        escalate: Optional[bool] = None,
        draft_reply: Optional[str] = None,
        error: Optional[str] = None,
    ):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO tickets (
                    created_at, client_id, channel, text,
                    category, confidence, escalate, draft_reply, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.datetime.now(datetime.UTC).isoformat(),
                    client_id,
                    channel,
                    text,
                    category,
                    confidence,
                    int(escalate) if escalate is not None else None,
                    draft_reply,
                    error,
                ),
            )
            conn.commit()