from __future__ import annotations

import os
import sqlite3
from datetime import datetime


class ConversationStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_user_time ON messages(user_id, created_at)"
            )

    def add_message(self, user_id: str, role: str, content: str):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO messages(user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (user_id, role, content, datetime.now().isoformat(timespec="seconds")),
            )

    def get_recent_messages(self, user_id: str, limit: int = 10) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content, created_at
                FROM messages
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return [
            {"role": role, "content": content, "created_at": created_at}
            for role, content, created_at in reversed(rows)
        ]
