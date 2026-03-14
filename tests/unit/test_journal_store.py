"""Tests for JournalStore SQLite wrapper."""

import pytest


def _make_store(tmp_path):
    from integrations.journal.store import JournalStore

    return JournalStore(tmp_path / "test_journal.db")


@pytest.mark.unit
class TestJournalStoreInit:
    def test_creates_db_file(self, tmp_path):
        _make_store(tmp_path)
        assert (tmp_path / "test_journal.db").exists()

    def test_creates_entries_table(self, tmp_path):
        import sqlite3

        _make_store(tmp_path)
        conn = sqlite3.connect(tmp_path / "test_journal.db")
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='entries'"
        )
        assert cursor.fetchone() is not None
        conn.close()


@pytest.mark.unit
class TestSaveAndGetEntry:
    def test_save_new_entry(self, tmp_path):
        store = _make_store(tmp_path)
        entry_id = store.save_entry(
            entry_date="2026-03-14",
            mode="freeform",
            mood="\U0001f60a",
            raw_text="had a great day",
            clean_text=None,
            prompt_used=None,
        )
        assert entry_id > 0

    def test_get_entry(self, tmp_path):
        store = _make_store(tmp_path)
        store.save_entry("2026-03-14", "freeform", "\U0001f60a", "great day", None, None)
        entry = store.get_entry("2026-03-14")
        assert entry is not None
        assert entry["date"] == "2026-03-14"
        assert entry["mode"] == "freeform"
        assert entry["mood"] == "\U0001f60a"
        assert entry["raw_text"] == "great day"

    def test_get_nonexistent_entry(self, tmp_path):
        store = _make_store(tmp_path)
        assert store.get_entry("2026-01-01") is None

    def test_upsert_preserves_created_at(self, tmp_path):
        store = _make_store(tmp_path)
        store.save_entry("2026-03-14", "freeform", None, "first", None, None)
        entry1 = store.get_entry("2026-03-14")

        store.save_entry("2026-03-14", "freeform", "\U0001f60a", "updated", None, None)
        entry2 = store.get_entry("2026-03-14")

        assert entry2["raw_text"] == "updated"
        assert entry2["mood"] == "\U0001f60a"
        assert entry2["created_at"] == entry1["created_at"]
        assert entry2["updated_at"] >= entry1["updated_at"]

    def test_delete_entry(self, tmp_path):
        store = _make_store(tmp_path)
        store.save_entry("2026-03-14", "freeform", None, "text", None, None)
        store.delete_entry("2026-03-14")
        assert store.get_entry("2026-03-14") is None


@pytest.mark.unit
class TestQueries:
    def test_get_entries_for_month(self, tmp_path):
        store = _make_store(tmp_path)
        store.save_entry("2026-03-01", "freeform", None, "a", None, None)
        store.save_entry("2026-03-15", "freeform", None, "b", None, None)
        store.save_entry("2026-04-01", "freeform", None, "c", None, None)
        entries = store.get_entries_for_month(2026, 3)
        assert len(entries) == 2
        dates = [e["date"] for e in entries]
        assert "2026-03-01" in dates
        assert "2026-03-15" in dates

    def test_get_total_count(self, tmp_path):
        store = _make_store(tmp_path)
        assert store.get_total_count() == 0
        store.save_entry("2026-03-14", "freeform", None, "a", None, None)
        store.save_entry("2026-03-15", "freeform", None, "b", None, None)
        assert store.get_total_count() == 2

    def test_get_streak_no_entries(self, tmp_path):
        store = _make_store(tmp_path)
        current, best = store.get_streak()
        assert current == 0
        assert best == 0

    def test_get_streak_consecutive_days(self, tmp_path):
        store = _make_store(tmp_path)
        store.save_entry("2026-03-12", "freeform", None, "a", None, None)
        store.save_entry("2026-03-13", "freeform", None, "b", None, None)
        store.save_entry("2026-03-14", "freeform", None, "c", None, None)
        current, best = store.get_streak()
        assert current >= 3
        assert best >= 3

    def test_get_mood_trend(self, tmp_path):
        store = _make_store(tmp_path)
        store.save_entry("2026-03-12", "freeform", "\U0001f60a", "a", None, None)
        store.save_entry("2026-03-13", "freeform", "\U0001f622", "b", None, None)
        store.save_entry("2026-03-14", "freeform", "\U0001f60a", "c", None, None)
        trend = store.get_mood_trend(7)
        assert len(trend) == 3
        assert trend[0]["mood"] == "\U0001f60a"
