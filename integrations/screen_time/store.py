"""SQLite storage for screen time sessions and app categories."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

from .defaults import NEUTRAL, get_default_categories


class ScreenTimeStore:
    """Wraps all SQLite operations for screen time tracking."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        self._seed_defaults()

    def _create_tables(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_sessions (
                id          TEXT PRIMARY KEY,
                app_name    TEXT NOT NULL,
                exe_name    TEXT NOT NULL,
                window_title TEXT,
                started_at  TEXT NOT NULL,
                ended_at    TEXT NOT NULL,
                duration_s  INTEGER NOT NULL
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_date ON app_sessions(started_at)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_app ON app_sessions(exe_name)"
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_categories (
                exe_name     TEXT PRIMARY KEY,
                category     TEXT NOT NULL DEFAULT 'Neutral',
                display_name TEXT,
                icon_color   TEXT
            )
            """
        )
        self._conn.commit()

    def _seed_defaults(self) -> None:
        defaults = get_default_categories()
        for exe_name, (category, display_name) in defaults.items():
            self._conn.execute(
                """
                INSERT OR IGNORE INTO app_categories (exe_name, category, display_name)
                VALUES (?, ?, ?)
                """,
                (exe_name, category, display_name),
            )
        self._conn.commit()

    def save_session(
        self,
        app_name: str,
        exe_name: str,
        window_title: str | None,
        started_at: datetime,
        ended_at: datetime,
    ) -> None:
        duration_s = int((ended_at - started_at).total_seconds())
        if duration_s < 1:
            return
        self._conn.execute(
            """
            INSERT INTO app_sessions (id, app_name, exe_name, window_title, started_at, ended_at, duration_s)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                app_name,
                exe_name,
                window_title,
                started_at.isoformat(),
                ended_at.isoformat(),
                duration_s,
            ),
        )
        self._conn.commit()

    def get_category(self, exe_name: str) -> str:
        cursor = self._conn.execute(
            "SELECT category FROM app_categories WHERE exe_name = ?", (exe_name,)
        )
        row = cursor.fetchone()
        return row["category"] if row else NEUTRAL

    def get_display_name(self, exe_name: str) -> str:
        cursor = self._conn.execute(
            "SELECT display_name FROM app_categories WHERE exe_name = ?", (exe_name,)
        )
        row = cursor.fetchone()
        return row["display_name"] if row and row["display_name"] else exe_name

    def update_category(self, exe_name: str, category: str, display_name: str | None = None) -> None:
        self._conn.execute(
            """
            INSERT INTO app_categories (exe_name, category, display_name)
            VALUES (?, ?, ?)
            ON CONFLICT(exe_name) DO UPDATE SET category = excluded.category, display_name = COALESCE(excluded.display_name, display_name)
            """,
            (exe_name, category, display_name),
        )
        self._conn.commit()

    def get_daily_total(self, day: str) -> int:
        """Total screen time in seconds for a given day."""
        next_day = (date.fromisoformat(day) + timedelta(days=1)).isoformat()
        cursor = self._conn.execute(
            "SELECT COALESCE(SUM(duration_s), 0) FROM app_sessions WHERE started_at >= ? AND started_at < ?",
            (day, next_day),
        )
        return cursor.fetchone()[0]

    def get_category_breakdown(self, day: str) -> dict[str, int]:
        """Category totals in seconds for a given day."""
        next_day = (date.fromisoformat(day) + timedelta(days=1)).isoformat()
        cursor = self._conn.execute(
            """
            SELECT COALESCE(c.category, 'Neutral') as category, SUM(s.duration_s) as total
            FROM app_sessions s
            LEFT JOIN app_categories c ON s.exe_name = c.exe_name
            WHERE s.started_at >= ? AND s.started_at < ?
            GROUP BY category ORDER BY total DESC
            """,
            (day, next_day),
        )
        return {row["category"]: row["total"] for row in cursor.fetchall()}

    def get_top_apps(self, day: str, limit: int = 10) -> list[dict]:
        next_day = (date.fromisoformat(day) + timedelta(days=1)).isoformat()
        cursor = self._conn.execute(
            """
            SELECT s.exe_name, s.app_name, SUM(s.duration_s) as total,
                   COALESCE(c.category, 'Neutral') as category,
                   COALESCE(c.display_name, s.app_name) as display_name
            FROM app_sessions s
            LEFT JOIN app_categories c ON s.exe_name = c.exe_name
            WHERE s.started_at >= ? AND s.started_at < ?
            GROUP BY s.exe_name ORDER BY total DESC LIMIT ?
            """,
            (day, next_day, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_timeline(self, day: str) -> list[dict]:
        next_day = (date.fromisoformat(day) + timedelta(days=1)).isoformat()
        cursor = self._conn.execute(
            """
            SELECT s.*, COALESCE(c.category, 'Neutral') as category,
                   COALESCE(c.display_name, s.app_name) as display_name
            FROM app_sessions s
            LEFT JOIN app_categories c ON s.exe_name = c.exe_name
            WHERE s.started_at >= ? AND s.started_at < ?
            ORDER BY s.started_at
            """,
            (day, next_day),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_weekly_totals(self, week_start: str) -> list[dict]:
        """Daily totals for a 7-day period starting from week_start."""
        ws = date.fromisoformat(week_start)
        result = []
        for i in range(7):
            d = (ws + timedelta(days=i)).isoformat()
            total = self.get_daily_total(d)
            breakdown = self.get_category_breakdown(d)
            result.append({"date": d, "total_s": total, "breakdown": breakdown})
        return result

    def get_top_apps_range(self, start_date: str, end_date: str, limit: int = 10) -> list[dict]:
        cursor = self._conn.execute(
            """
            SELECT s.exe_name, s.app_name, SUM(s.duration_s) as total,
                   COALESCE(c.category, 'Neutral') as category,
                   COALESCE(c.display_name, s.app_name) as display_name
            FROM app_sessions s
            LEFT JOIN app_categories c ON s.exe_name = c.exe_name
            WHERE s.started_at >= ? AND s.started_at < ?
            GROUP BY s.exe_name ORDER BY total DESC LIMIT ?
            """,
            (start_date, end_date, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_all_categories(self) -> list[dict]:
        cursor = self._conn.execute("SELECT * FROM app_categories ORDER BY exe_name")
        return [dict(row) for row in cursor.fetchall()]

    def prune_old_data(self, retention_days: int) -> None:
        cutoff = (date.today() - timedelta(days=retention_days)).isoformat()
        self._conn.execute("DELETE FROM app_sessions WHERE started_at < ?", (cutoff,))
        self._conn.commit()

    def clear_all(self) -> None:
        self._conn.execute("DELETE FROM app_sessions")
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
