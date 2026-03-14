"""SQLite storage for journal entries."""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path


class JournalStore:
    """Wraps all SQLite operations for journal entries."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT NOT NULL UNIQUE,
                mode        TEXT NOT NULL,
                mood        TEXT,
                raw_text    TEXT NOT NULL,
                clean_text  TEXT,
                prompt_used TEXT,
                created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        self._conn.commit()

    def save_entry(
        self,
        date: str,
        mode: str,
        mood: str | None,
        raw_text: str,
        clean_text: str | None,
        prompt_used: str | None,
    ) -> int:
        """Insert or update an entry. Returns the entry id."""
        cursor = self._conn.execute(
            """
            INSERT INTO entries (date, mode, mood, raw_text, clean_text, prompt_used)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                mode = excluded.mode,
                mood = excluded.mood,
                raw_text = excluded.raw_text,
                clean_text = excluded.clean_text,
                prompt_used = excluded.prompt_used,
                updated_at = CURRENT_TIMESTAMP
            """,
            (date, mode, mood, raw_text, clean_text, prompt_used),
        )
        self._conn.commit()
        return cursor.lastrowid

    def get_entry(self, date: str) -> dict | None:
        """Get a single entry by date."""
        cursor = self._conn.execute("SELECT * FROM entries WHERE date = ?", (date,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_entries_for_month(self, year: int, month: int) -> list[dict]:
        """Get all entries for a given month."""
        prefix = f"{year:04d}-{month:02d}"
        cursor = self._conn.execute(
            "SELECT * FROM entries WHERE date LIKE ? ORDER BY date",
            (f"{prefix}%",),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_streak(self) -> tuple[int, int]:
        """Return (current_streak, best_streak) counting consecutive days."""
        cursor = self._conn.execute("SELECT date FROM entries ORDER BY date DESC")
        dates = [row["date"] for row in cursor.fetchall()]

        if not dates:
            return (0, 0)

        parsed = sorted([date.fromisoformat(d) for d in dates], reverse=True)

        # Current streak: count consecutive days from today backwards
        today = date.today()
        current = 0
        check = today
        for d in parsed:
            if d == check:
                current += 1
                check -= timedelta(days=1)
            elif d < check:
                break

        # Best streak: scan all dates for longest consecutive run
        sorted_asc = sorted(parsed)
        best = 1 if sorted_asc else 0
        run = 1
        for i in range(1, len(sorted_asc)):
            if sorted_asc[i] - sorted_asc[i - 1] == timedelta(days=1):
                run += 1
                best = max(best, run)
            else:
                run = 1

        return (current, best)

    def get_mood_trend(self, days: int) -> list[dict]:
        """Get entries with mood set from the last N days."""
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        cursor = self._conn.execute(
            "SELECT date, mood FROM entries WHERE mood IS NOT NULL AND date >= ? ORDER BY date",
            (cutoff,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_total_count(self) -> int:
        """Total number of entries."""
        cursor = self._conn.execute("SELECT COUNT(*) FROM entries")
        return cursor.fetchone()[0]

    def delete_entry(self, date: str) -> None:
        """Delete an entry by date."""
        self._conn.execute("DELETE FROM entries WHERE date = ?", (date,))
        self._conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
