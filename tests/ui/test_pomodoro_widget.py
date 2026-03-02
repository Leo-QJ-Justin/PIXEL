"""Tests for PomodoroWidget and helper widgets."""

import sys

import pytest
from PyQt6.QtWidgets import QApplication

from integrations.pomodoro.integration import PomodoroIntegration
from src.ui.pomodoro_widget import (
    DiamondStreak,
    PomodoroWidget,
    ProgressRing,
    WeeklyChart,
)

# Ensure a QApplication exists for widget tests
_app = QApplication.instance() or QApplication(sys.argv)


def _make_integration(tmp_path, settings=None):
    """Create a PomodoroIntegration with a tick timer ready."""
    path = tmp_path / "pomodoro"
    path.mkdir(exist_ok=True)
    i = PomodoroIntegration(path, settings or {})
    from PyQt6.QtCore import QTimer

    i._tick_timer = QTimer()
    i._tick_timer.setInterval(1000)
    i._tick_timer.timeout.connect(i._on_tick)
    return i


@pytest.mark.ui
class TestPomodoroWidgetInit:
    def test_creates_without_error(self, tmp_path):
        i = _make_integration(tmp_path)
        w = PomodoroWidget(i)
        assert w is not None

    def test_has_frameless_flag(self, tmp_path):
        from PyQt6.QtCore import Qt

        i = _make_integration(tmp_path)
        w = PomodoroWidget(i)
        assert w.windowFlags() & Qt.WindowType.FramelessWindowHint

    def test_has_tool_flag(self, tmp_path):
        from PyQt6.QtCore import Qt

        i = _make_integration(tmp_path)
        w = PomodoroWidget(i)
        assert w.windowFlags() & Qt.WindowType.Tool

    def test_starts_with_idle_buttons(self, tmp_path):
        i = _make_integration(tmp_path)
        w = PomodoroWidget(i)
        # Use isHidden() since widget may not be shown (isVisible checks parent chain)
        assert not w._start_btn.isHidden()
        assert w._pause_btn.isHidden()
        assert w._skip_btn.isHidden()
        assert w._break_btn.isHidden()
        assert w._skip_break_btn.isHidden()

    def test_initial_phase_label(self, tmp_path):
        i = _make_integration(tmp_path)
        w = PomodoroWidget(i)
        assert w._phase_label.text() == "Ready to focus?"

    def test_initial_countdown(self, tmp_path):
        i = _make_integration(tmp_path)
        w = PomodoroWidget(i)
        assert w._countdown_label.text() == "00:00"


@pytest.mark.ui
class TestWidgetStateTransitions:
    def test_focus_updates_ui(self, tmp_path):
        i = _make_integration(tmp_path, {"work_duration_minutes": 10})
        w = PomodoroWidget(i)
        i.start_session()
        assert w._phase_label.text() == "FOCUSING..."
        assert w._countdown_label.text() == "10:00"
        assert w._start_btn.isHidden()
        assert not w._pause_btn.isHidden()
        assert not w._skip_btn.isHidden()

    def test_session_complete_updates_ui(self, tmp_path):
        i = _make_integration(tmp_path)
        w = PomodoroWidget(i)
        i.start_session()
        i.skip()
        assert w._phase_label.text() == "SESSION CLEAR!"
        assert not w._break_btn.isHidden()
        assert not w._skip_break_btn.isHidden()

    def test_break_updates_ui(self, tmp_path):
        i = _make_integration(tmp_path, {"short_break_minutes": 3})
        w = PomodoroWidget(i)
        i.start_session()
        i.skip()
        i.start_break()
        assert w._phase_label.text() == "RESTING..."
        assert w._countdown_label.text() == "03:00"
        assert not w._pause_btn.isHidden()

    def test_idle_after_skip_break(self, tmp_path):
        i = _make_integration(tmp_path)
        w = PomodoroWidget(i)
        i.start_session()
        i.skip()
        i.skip_break()
        assert w._phase_label.text() == "Ready to focus?"
        assert not w._start_btn.isHidden()

    def test_diamond_fills_on_session_complete(self, tmp_path):
        i = _make_integration(tmp_path)
        w = PomodoroWidget(i)
        i.start_session()
        i.skip()
        assert w._diamonds._filled == 1


@pytest.mark.ui
class TestWidgetTick:
    def test_tick_updates_countdown(self, tmp_path):
        i = _make_integration(tmp_path, {"work_duration_minutes": 1})
        w = PomodoroWidget(i)
        i.start_session()
        i._on_tick()
        assert w._countdown_label.text() == "00:59"

    def test_tick_updates_ring_progress(self, tmp_path):
        i = _make_integration(tmp_path, {"work_duration_minutes": 1})
        w = PomodoroWidget(i)
        i.start_session()
        i._on_tick()
        # 59/60 remaining
        assert 0.98 < w._ring._progress < 0.99


@pytest.mark.ui
class TestWidgetPause:
    def test_pause_changes_button_text(self, tmp_path):
        i = _make_integration(tmp_path)
        w = PomodoroWidget(i)
        i.start_session()
        w._on_pause_clicked()
        assert w._pause_btn.text() == "RESUME"

    def test_resume_changes_button_text(self, tmp_path):
        i = _make_integration(tmp_path)
        w = PomodoroWidget(i)
        i.start_session()
        w._on_pause_clicked()  # pause
        w._on_pause_clicked()  # resume
        assert w._pause_btn.text() == "PAUSE"


@pytest.mark.ui
class TestWidgetStats:
    def test_stats_update_today_label(self, tmp_path):
        from datetime import date

        i = _make_integration(tmp_path)
        w = PomodoroWidget(i)
        today = date.today().isoformat()
        w._on_stats_updated(
            {
                "total_sessions": 5,
                "daily": {today: 3},
                "current_streak_days": 2,
                "longest_streak_days": 4,
            }
        )
        assert "3" in w._today_label.text()
        assert "2" in w._streak_label.text()
        assert "5" in w._total_label.text()


@pytest.mark.ui
class TestProgressRing:
    def test_initial_progress(self):
        ring = ProgressRing()
        assert ring._progress == 1.0

    def test_set_progress_clamps(self):
        ring = ProgressRing()
        ring.set_progress(1.5)
        assert ring._progress == 1.0
        ring.set_progress(-0.5)
        assert ring._progress == 0.0

    def test_set_progress_normal(self):
        ring = ProgressRing()
        ring.set_progress(0.5)
        assert ring._progress == 0.5


@pytest.mark.ui
class TestDiamondStreak:
    def test_default_count(self):
        ds = DiamondStreak()
        assert ds._count == 4
        assert ds._filled == 0

    def test_set_filled(self):
        ds = DiamondStreak(4)
        ds.set_filled(3)
        assert ds._filled == 3

    def test_set_count(self):
        ds = DiamondStreak(4)
        ds.set_count(6)
        assert ds._count == 6


@pytest.mark.ui
class TestWeeklyChart:
    def test_set_data(self):
        chart = WeeklyChart()
        chart.set_data({"2026-03-02": 5})
        assert chart._data == {"2026-03-02": 5}
