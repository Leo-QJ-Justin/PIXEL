"""Tests for the Pomodoro timer integration."""

import json
from datetime import date

import pytest

import integrations.pomodoro.integration  # noqa: F401 (needed for patch targets)
from integrations.pomodoro.integration import PomodoroIntegration, PomodoroState


def _make_integration(tmp_path, settings=None):
    """Helper to create a PomodoroIntegration instance."""
    integration_path = tmp_path / "pomodoro"
    integration_path.mkdir(exist_ok=True)
    return PomodoroIntegration(integration_path, settings or {})


@pytest.mark.unit
class TestPomodoroInit:
    def test_name(self, tmp_path):
        i = _make_integration(tmp_path)
        assert i.name == "pomodoro"

    def test_display_name(self, tmp_path):
        i = _make_integration(tmp_path)
        assert i.display_name == "Pomodoro Timer"

    def test_default_settings(self, tmp_path):
        i = _make_integration(tmp_path)
        d = i.get_default_settings()
        assert d["work_duration_minutes"] == 25
        assert d["short_break_minutes"] == 5
        assert d["long_break_minutes"] == 15
        assert d["sessions_per_cycle"] == 4
        assert d["enabled"] is True

    def test_initial_state_is_idle(self, tmp_path):
        i = _make_integration(tmp_path)
        assert i.state == PomodoroState.IDLE

    def test_initial_remaining_is_zero(self, tmp_path):
        i = _make_integration(tmp_path)
        assert i._remaining_seconds == 0

    def test_settings_override(self, tmp_path):
        i = _make_integration(tmp_path, {"work_duration_minutes": 50})
        assert i._settings["work_duration_minutes"] == 50


@pytest.mark.unit
class TestStateMachine:
    def _started_integration(self, tmp_path, settings=None):
        """Create an integration with tick timer initialized."""
        i = _make_integration(tmp_path, settings)
        # Manually create the timer (normally done in async start())
        from PyQt6.QtCore import QTimer

        i._tick_timer = QTimer()
        i._tick_timer.setInterval(1000)
        i._tick_timer.timeout.connect(i._on_tick)
        return i

    def test_start_session_transitions_to_focus(self, tmp_path):
        i = self._started_integration(tmp_path)
        states = []
        i.state_changed.connect(lambda s, ctx: states.append(s))
        i.start_session()
        assert states == ["FOCUS"]
        assert i.state == PomodoroState.FOCUS

    def test_start_session_sets_remaining(self, tmp_path):
        i = self._started_integration(tmp_path, {"work_duration_minutes": 10})
        i.start_session()
        assert i._remaining_seconds == 600

    def test_start_session_ignored_during_focus(self, tmp_path):
        i = self._started_integration(tmp_path)
        i.start_session()
        states = []
        i.state_changed.connect(lambda s, ctx: states.append(s))
        i.start_session()  # should be ignored
        assert states == []

    def test_skip_during_focus_goes_to_session_complete(self, tmp_path):
        i = self._started_integration(tmp_path)
        i.start_session()
        states = []
        i.state_changed.connect(lambda s, ctx: states.append(s))
        i.skip()
        assert states == ["SESSION_COMPLETE"]

    def test_start_break_goes_to_short_break(self, tmp_path):
        i = self._started_integration(tmp_path)
        i.start_session()
        i.skip()  # -> SESSION_COMPLETE
        states = []
        i.state_changed.connect(lambda s, ctx: states.append(s))
        i.start_break()
        assert states == ["SHORT_BREAK"]

    def test_start_break_sets_remaining(self, tmp_path):
        i = self._started_integration(tmp_path, {"short_break_minutes": 3})
        i.start_session()
        i.skip()
        i.start_break()
        assert i._remaining_seconds == 180

    def test_skip_break_returns_to_idle(self, tmp_path):
        i = self._started_integration(tmp_path)
        i.start_session()
        i.skip()
        states = []
        i.state_changed.connect(lambda s, ctx: states.append(s))
        i.skip_break()
        assert states == ["IDLE"]

    def test_long_break_after_full_cycle(self, tmp_path):
        i = self._started_integration(tmp_path, {"sessions_per_cycle": 2})
        # Complete 2 sessions
        for _ in range(2):
            i.start_session()
            i.skip()  # -> SESSION_COMPLETE, records session
            if i.state == PomodoroState.SESSION_COMPLETE:
                if i._completed_in_cycle < 2:
                    i.start_break()
                    i.skip()  # skip break -> IDLE

        # Now at SESSION_COMPLETE with 2 completed
        assert i._completed_in_cycle == 2
        states = []
        i.state_changed.connect(lambda s, ctx: states.append(s))
        i.start_break()
        assert states == ["LONG_BREAK"]

    def test_long_break_resets_cycle_count(self, tmp_path):
        i = self._started_integration(tmp_path, {"sessions_per_cycle": 1})
        i.start_session()
        i.skip()  # -> SESSION_COMPLETE (completed_in_cycle = 1)
        i.start_break()  # -> LONG_BREAK
        # Simulate break ending
        i._remaining_seconds = 1
        i._on_tick()  # -> IDLE (resets cycle)
        assert i._completed_in_cycle == 0

    def test_auto_start_resumes_focus_after_break(self, tmp_path):
        i = self._started_integration(tmp_path, {"auto_start": True})
        i.start_session()
        i.skip()  # -> SESSION_COMPLETE
        i.start_break()  # -> SHORT_BREAK
        states = []
        i.state_changed.connect(lambda s, ctx: states.append(s))
        # Simulate break ending
        i._remaining_seconds = 1
        i._on_tick()
        assert "FOCUS" in states

    def test_skip_during_break_goes_to_idle(self, tmp_path):
        i = self._started_integration(tmp_path)
        i.start_session()
        i.skip()
        i.start_break()  # -> SHORT_BREAK
        states = []
        i.state_changed.connect(lambda s, ctx: states.append(s))
        i.skip()
        assert "IDLE" in states


@pytest.mark.unit
class TestPause:
    def _started_integration(self, tmp_path, settings=None):
        i = _make_integration(tmp_path, settings)
        from PyQt6.QtCore import QTimer

        i._tick_timer = QTimer()
        i._tick_timer.setInterval(1000)
        i._tick_timer.timeout.connect(i._on_tick)
        return i

    def test_pause_sets_flag(self, tmp_path):
        i = self._started_integration(tmp_path)
        i.start_session()
        i.pause()
        assert i._paused is True

    def test_resume_clears_flag(self, tmp_path):
        i = self._started_integration(tmp_path)
        i.start_session()
        i.pause()
        i.pause()  # toggle resume
        assert i._paused is False

    def test_tick_ignored_while_paused(self, tmp_path):
        i = self._started_integration(tmp_path, {"work_duration_minutes": 1})
        i.start_session()
        before = i._remaining_seconds
        i.pause()
        i._on_tick()
        assert i._remaining_seconds == before  # no decrement

    def test_pause_ignored_in_idle(self, tmp_path):
        i = self._started_integration(tmp_path)
        i.pause()
        assert i._paused is False


@pytest.mark.unit
class TestTimerTick:
    def _started_integration(self, tmp_path, settings=None):
        i = _make_integration(tmp_path, settings)
        from PyQt6.QtCore import QTimer

        i._tick_timer = QTimer()
        i._tick_timer.setInterval(1000)
        i._tick_timer.timeout.connect(i._on_tick)
        return i

    def test_tick_emits_remaining(self, tmp_path):
        i = self._started_integration(tmp_path, {"work_duration_minutes": 1})
        i.start_session()
        ticks = []
        i.timer_tick.connect(lambda s: ticks.append(s))
        i._on_tick()
        assert ticks == [59]

    def test_tick_decrements(self, tmp_path):
        i = self._started_integration(tmp_path, {"work_duration_minutes": 1})
        i.start_session()
        i._on_tick()
        i._on_tick()
        assert i._remaining_seconds == 58

    def test_tick_to_zero_triggers_session_complete(self, tmp_path):
        i = self._started_integration(tmp_path)
        i.start_session()
        i._remaining_seconds = 1
        states = []
        i.state_changed.connect(lambda s, ctx: states.append(s))
        i._on_tick()
        assert "SESSION_COMPLETE" in states

    def test_break_tick_to_zero_transitions(self, tmp_path):
        i = self._started_integration(tmp_path)
        i.start_session()
        i.skip()
        i.start_break()  # -> SHORT_BREAK
        i._remaining_seconds = 1
        states = []
        i.state_changed.connect(lambda s, ctx: states.append(s))
        i._on_tick()
        assert "IDLE" in states


@pytest.mark.unit
class TestBehaviorTriggers:
    def _started_integration(self, tmp_path, settings=None):
        i = _make_integration(tmp_path, settings)
        from PyQt6.QtCore import QTimer

        i._tick_timer = QTimer()
        i._tick_timer.setInterval(1000)
        i._tick_timer.timeout.connect(i._on_tick)
        return i

    def test_focus_triggers_behavior(self, tmp_path):
        i = self._started_integration(tmp_path)
        behaviors = []
        i.request_behavior.connect(lambda name, ctx: behaviors.append(name))
        i.start_session()
        assert "focus" in behaviors

    def test_session_complete_sends_notification(self, tmp_path):
        i = self._started_integration(tmp_path)
        notifications = []
        i.request_notification.connect(lambda ctx: notifications.append(ctx))
        i.start_session()
        i.skip()
        assert any("complete" in n.get("bubble_text", "").lower() for n in notifications)

    def test_break_sends_notification(self, tmp_path):
        i = self._started_integration(tmp_path)
        notifications = []
        i.request_notification.connect(lambda ctx: notifications.append(ctx))
        i.start_session()
        i.skip()
        i.start_break()
        assert any("break" in n.get("bubble_text", "").lower() for n in notifications)


@pytest.mark.unit
class TestStatsTracking:
    def _started_integration(self, tmp_path, settings=None):
        i = _make_integration(tmp_path, settings)
        from PyQt6.QtCore import QTimer

        i._tick_timer = QTimer()
        i._tick_timer.setInterval(1000)
        i._tick_timer.timeout.connect(i._on_tick)
        return i

    def test_session_complete_increments_total(self, tmp_path):
        i = self._started_integration(tmp_path)
        i.start_session()
        i.skip()
        assert i._stats["total_sessions"] == 1

    def test_multiple_sessions_accumulate(self, tmp_path):
        i = self._started_integration(tmp_path)
        for _ in range(3):
            i.start_session()
            i.skip()
            i.skip_break()
        assert i._stats["total_sessions"] == 3

    def test_daily_count_tracked(self, tmp_path):
        i = self._started_integration(tmp_path)
        i.start_session()
        i.skip()
        today = date.today().isoformat()
        assert i._stats["daily"][today] == 1

    def test_stats_persist_to_file(self, tmp_path):
        i = self._started_integration(tmp_path)
        i.start_session()
        i.skip()
        stats_file = tmp_path / "pomodoro" / "stats.json"
        assert stats_file.exists()
        data = json.loads(stats_file.read_text())
        assert data["total_sessions"] == 1

    def test_stats_load_from_file(self, tmp_path):
        stats_file = tmp_path / "pomodoro" / "stats.json"
        (tmp_path / "pomodoro").mkdir(exist_ok=True)
        stats_file.write_text(
            json.dumps(
                {
                    "total_sessions": 42,
                    "daily": {},
                    "current_streak_days": 5,
                    "longest_streak_days": 10,
                }
            )
        )
        i = _make_integration(tmp_path)
        assert i._stats["total_sessions"] == 42
        assert i._stats["current_streak_days"] == 5

    def test_streak_increments_on_consecutive_days(self, tmp_path):
        (tmp_path / "pomodoro").mkdir(exist_ok=True)
        today = date.today()
        yesterday = date.fromordinal(today.toordinal() - 1)
        stats_file = tmp_path / "pomodoro" / "stats.json"
        stats_file.write_text(
            json.dumps(
                {
                    "total_sessions": 5,
                    "daily": {yesterday.isoformat(): 3},
                    "current_streak_days": 1,
                    "longest_streak_days": 1,
                }
            )
        )
        i = self._started_integration(tmp_path)
        i.start_session()
        i.skip()
        assert i._stats["current_streak_days"] == 2
        assert i._stats["longest_streak_days"] == 2

    def test_corrupted_stats_file_uses_defaults(self, tmp_path):
        stats_file = tmp_path / "pomodoro" / "stats.json"
        (tmp_path / "pomodoro").mkdir(exist_ok=True)
        stats_file.write_text("not valid json{{{")
        i = _make_integration(tmp_path)
        assert i._stats["total_sessions"] == 0


@pytest.mark.unit
class TestStartStop:
    def test_start_creates_timer(self, tmp_path):
        import asyncio

        i = _make_integration(tmp_path)
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(i.start())
            assert i._tick_timer is not None
        finally:
            loop.close()

    def test_stop_clears_timer(self, tmp_path):
        import asyncio

        i = _make_integration(tmp_path)
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(i.start())
            loop.run_until_complete(i.stop())
            assert i._tick_timer is None
        finally:
            loop.close()

    def test_stop_saves_stats(self, tmp_path):
        import asyncio

        i = _make_integration(tmp_path)
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(i.start())
            i._stats["total_sessions"] = 99
            loop.run_until_complete(i.stop())
        finally:
            loop.close()
        stats_file = tmp_path / "pomodoro" / "stats.json"
        data = json.loads(stats_file.read_text())
        assert data["total_sessions"] == 99
