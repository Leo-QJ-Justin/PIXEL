"""Tests for default habit seeding on first launch."""

from pathlib import Path

from integrations.habits.store import HabitStore


def test_new_db_seeds_default_habits(tmp_path: Path):
    """A freshly created database should contain the 4 default habits."""
    store = HabitStore(tmp_path / "habits.db")
    habits = store.list_habits()
    assert len(habits) == 4
    titles = [h["title"] for h in habits]
    assert titles == ["Drink Water", "Exercise", "Read", "Take a Break"]
    icons = [h["icon"] for h in habits]
    assert icons == ["💧", "🏋️", "📖", "🧘"]
    # All should be daily with target_count 1
    for h in habits:
        assert h["frequency"] == "daily"
        assert h["target_count"] == 1
    store.close()


def test_existing_db_does_not_reseed(tmp_path: Path):
    """Opening an existing database should not re-add defaults."""
    db_path = tmp_path / "habits.db"
    store = HabitStore(db_path)
    # Delete all habits
    for h in store.list_habits():
        store.delete_habit(h["id"])
    assert len(store.list_habits()) == 0
    store.close()

    # Re-open — should NOT re-seed
    store2 = HabitStore(db_path)
    assert len(store2.list_habits()) == 0
    store2.close()
