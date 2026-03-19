"""SQLite storage for tasks."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime
from pathlib import Path


class TaskStore:
    """Wraps all SQLite operations for tasks."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id           TEXT PRIMARY KEY,
                title        TEXT NOT NULL,
                notes        TEXT,
                completed    INTEGER NOT NULL DEFAULT 0,
                due_date     TEXT,
                tag          TEXT,
                priority     INTEGER NOT NULL DEFAULT 0,
                parent_id    TEXT REFERENCES tasks(id) ON DELETE CASCADE,
                sort_order   INTEGER NOT NULL DEFAULT 0,
                created_at   TEXT NOT NULL,
                completed_at TEXT
            )
            """
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_id)")
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date) WHERE completed = 0"
        )
        self._conn.commit()

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        d = dict(row)
        d["completed"] = bool(d["completed"])
        return d

    def list_tasks(self, include_completed: bool = False) -> list[dict]:
        if include_completed:
            cursor = self._conn.execute("SELECT * FROM tasks ORDER BY sort_order, created_at")
        else:
            cursor = self._conn.execute(
                "SELECT * FROM tasks WHERE completed = 0 ORDER BY sort_order, created_at"
            )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_task(self, task_id: str) -> dict | None:
        cursor = self._conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        return self._row_to_dict(row) if row else None

    def create_task(
        self,
        title: str,
        due_date: str | None = None,
        tag: str | None = None,
        priority: int = 0,
        parent_id: str | None = None,
        notes: str | None = None,
    ) -> dict:
        task_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        # Get next sort order
        cursor = self._conn.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM tasks")
        sort_order = cursor.fetchone()[0]

        self._conn.execute(
            """
            INSERT INTO tasks (id, title, notes, due_date, tag, priority, parent_id, sort_order, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (task_id, title, notes, due_date, tag, priority, parent_id, sort_order, now),
        )
        self._conn.commit()
        return self.get_task(task_id)  # type: ignore

    def update_task(self, task_id: str, **fields) -> dict | None:
        allowed = {"title", "notes", "due_date", "tag", "priority", "parent_id", "sort_order"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return self.get_task(task_id)
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [task_id]
        self._conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
        self._conn.commit()
        return self.get_task(task_id)

    def complete_task(self, task_id: str) -> dict | None:
        now = datetime.now().isoformat()
        self._conn.execute(
            "UPDATE tasks SET completed = 1, completed_at = ? WHERE id = ?",
            (now, task_id),
        )
        self._conn.commit()
        return self.get_task(task_id)

    def uncomplete_task(self, task_id: str) -> dict | None:
        self._conn.execute(
            "UPDATE tasks SET completed = 0, completed_at = NULL WHERE id = ?",
            (task_id,),
        )
        self._conn.commit()
        return self.get_task(task_id)

    def delete_task(self, task_id: str) -> None:
        self._conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self._conn.commit()

    def reorder_tasks(self, task_ids: list[str]) -> None:
        for i, tid in enumerate(task_ids):
            self._conn.execute("UPDATE tasks SET sort_order = ? WHERE id = ?", (i, tid))
        self._conn.commit()

    def get_overdue_tasks(self) -> list[dict]:
        today = date.today().isoformat()
        cursor = self._conn.execute(
            "SELECT * FROM tasks WHERE completed = 0 AND due_date IS NOT NULL AND due_date < ? ORDER BY due_date",
            (today,),
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_today_tasks(self) -> list[dict]:
        today = date.today().isoformat()
        cursor = self._conn.execute(
            "SELECT * FROM tasks WHERE completed = 0 AND due_date = ? ORDER BY sort_order",
            (today,),
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def close(self) -> None:
        self._conn.close()
