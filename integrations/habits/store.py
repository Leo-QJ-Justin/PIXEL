"""SQLite storage for habits and completions."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path


class HabitStore:
    """Wraps all SQLite operations for habits."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS habits (
                id            TEXT PRIMARY KEY,
                title         TEXT NOT NULL,
                icon          TEXT NOT NULL DEFAULT '✅',
                frequency     TEXT NOT NULL DEFAULT 'daily',
                target_count  INTEGER NOT NULL DEFAULT 1,
                reminder_time TEXT,
                sort_order    INTEGER NOT NULL DEFAULT 0,
                created_at    TEXT NOT NULL,
                archived      INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS habit_completions (
                id        TEXT PRIMARY KEY,
                habit_id  TEXT NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
                date      TEXT NOT NULL,
                UNIQUE(habit_id, date)
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_completions_habit_date ON habit_completions(habit_id, date)"
        )
        self._conn.commit()

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        d = dict(row)
        d["archived"] = bool(d.get("archived", 0))
        return d

    def list_habits(self, include_archived: bool = False) -> list[dict]:
        if include_archived:
            cursor = self._conn.execute("SELECT * FROM habits ORDER BY sort_order")
        else:
            cursor = self._conn.execute(
                "SELECT * FROM habits WHERE archived = 0 ORDER BY sort_order"
            )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def create_habit(
        self,
        title: str,
        icon: str = "✅",
        frequency: str = "daily",
        target_count: int = 1,
        reminder_time: str | None = None,
    ) -> dict:
        habit_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        cursor = self._conn.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM habits")
        sort_order = cursor.fetchone()[0]
        self._conn.execute(
            """
            INSERT INTO habits (id, title, icon, frequency, target_count, reminder_time, sort_order, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (habit_id, title, icon, frequency, target_count, reminder_time, sort_order, now),
        )
        self._conn.commit()
        return self._row_to_dict(self._conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone())

    def update_habit(self, habit_id: str, **fields) -> dict | None:
        allowed = {"title", "icon", "frequency", "target_count", "reminder_time", "sort_order"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            row = self._conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
            return self._row_to_dict(row) if row else None
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [habit_id]
        self._conn.execute(f"UPDATE habits SET {set_clause} WHERE id = ?", values)
        self._conn.commit()
        row = self._conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def archive_habit(self, habit_id: str) -> None:
        self._conn.execute("UPDATE habits SET archived = 1 WHERE id = ?", (habit_id,))
        self._conn.commit()

    def delete_habit(self, habit_id: str) -> None:
        self._conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        self._conn.commit()

    def complete_today(self, habit_id: str) -> None:
        today = date.today().isoformat()
        comp_id = str(uuid.uuid4())
        try:
            self._conn.execute(
                "INSERT INTO habit_completions (id, habit_id, date) VALUES (?, ?, ?)",
                (comp_id, habit_id, today),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                pass  # Already completed today
            else:
                raise

    def uncomplete_today(self, habit_id: str) -> None:
        today = date.today().isoformat()
        self._conn.execute(
            "DELETE FROM habit_completions WHERE habit_id = ? AND date = ?",
            (habit_id, today),
        )
        self._conn.commit()

    def is_completed_today(self, habit_id: str) -> bool:
        today = date.today().isoformat()
        cursor = self._conn.execute(
            "SELECT 1 FROM habit_completions WHERE habit_id = ? AND date = ?",
            (habit_id, today),
        )
        return cursor.fetchone() is not None

    def get_streak(self, habit_id: str) -> int:
        """Get current streak for a habit. For daily: consecutive days. For weekly/x_per_week: consecutive qualifying weeks."""
        habit = self._conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
        if not habit:
            return 0

        freq = habit["frequency"]
        if freq == "daily":
            return self._daily_streak(habit_id)
        else:
            return self._weekly_streak(habit_id, habit["target_count"] if freq == "x_per_week" else 1)

    def _daily_streak(self, habit_id: str) -> int:
        cursor = self._conn.execute(
            "SELECT DISTINCT date FROM habit_completions WHERE habit_id = ? ORDER BY date DESC",
            (habit_id,),
        )
        dates = [row["date"] for row in cursor.fetchall()]
        if not dates:
            return 0

        streak = 0
        check = date.today()
        # Allow today to not be completed yet (streak continues from yesterday)
        if dates[0] != check.isoformat():
            check -= timedelta(days=1)

        for d_str in dates:
            d = date.fromisoformat(d_str)
            if d == check:
                streak += 1
                check -= timedelta(days=1)
            elif d < check:
                break
        return streak

    def _weekly_streak(self, habit_id: str, target: int) -> int:
        """Count consecutive weeks meeting the target completions."""
        cursor = self._conn.execute(
            "SELECT date FROM habit_completions WHERE habit_id = ? ORDER BY date DESC",
            (habit_id,),
        )
        dates = [date.fromisoformat(row["date"]) for row in cursor.fetchall()]
        if not dates:
            return 0

        def week_start(d: date) -> date:
            return d - timedelta(days=d.weekday())  # Monday

        # Group by week
        weeks: dict[date, int] = {}
        for d in dates:
            ws = week_start(d)
            weeks[ws] = weeks.get(ws, 0) + 1

        streak = 0
        current_week = week_start(date.today())
        # If current week hasn't ended and hasn't met target, skip it (same as daily streak logic)
        if current_week in weeks and weeks[current_week] < target and date.today().weekday() < 6:
            current_week -= timedelta(weeks=1)
        while current_week in weeks:
            if weeks[current_week] >= target:
                streak += 1
            else:
                break
            current_week -= timedelta(weeks=1)
        return streak

    def get_longest_streak(self, habit_id: str) -> int:
        cursor = self._conn.execute(
            "SELECT DISTINCT date FROM habit_completions WHERE habit_id = ? ORDER BY date",
            (habit_id,),
        )
        dates = [date.fromisoformat(row["date"]) for row in cursor.fetchall()]
        if not dates:
            return 0
        best = 1
        run = 1
        for i in range(1, len(dates)):
            if dates[i] - dates[i - 1] == timedelta(days=1):
                run += 1
                best = max(best, run)
            else:
                run = 1
        return best

    def get_completion_rate(self, habit_id: str, days: int = 30) -> float:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        cursor = self._conn.execute(
            "SELECT COUNT(DISTINCT date) FROM habit_completions WHERE habit_id = ? AND date >= ?",
            (habit_id, cutoff),
        )
        count = cursor.fetchone()[0]
        return count / days if days > 0 else 0.0

    def get_week_completions(self, habit_id: str, week_start_str: str) -> list[str]:
        ws = date.fromisoformat(week_start_str)
        we = ws + timedelta(days=6)
        cursor = self._conn.execute(
            "SELECT date FROM habit_completions WHERE habit_id = ? AND date >= ? AND date <= ? ORDER BY date",
            (habit_id, ws.isoformat(), we.isoformat()),
        )
        return [row["date"] for row in cursor.fetchall()]

    def get_week_progress(self, habit_id: str) -> int:
        """Get number of completions this week (Mon-Sun)."""
        today = date.today()
        ws = today - timedelta(days=today.weekday())
        return len(self.get_week_completions(habit_id, ws.isoformat()))

    def get_today_status(self) -> list[dict]:
        """Get all active habits with their today completion status, streak, and week progress."""
        habits = self.list_habits(include_archived=False)
        result = []
        for h in habits:
            result.append({
                **h,
                "completed_today": self.is_completed_today(h["id"]),
                "streak": self.get_streak(h["id"]),
                "week_progress": self.get_week_progress(h["id"]),
                "week_target": h["target_count"],
            })
        return result

    def get_habit(self, habit_id: str) -> dict | None:
        row = self._conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def get_total_completions(self, habit_id: str) -> int:
        cursor = self._conn.execute(
            "SELECT COUNT(*) FROM habit_completions WHERE habit_id = ?", (habit_id,)
        )
        return cursor.fetchone()[0]

    def close(self) -> None:
        self._conn.close()
