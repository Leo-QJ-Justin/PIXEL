"""Tests for DashboardHost base class."""

import pytest
from PyQt6.QtWidgets import QLabel


def _make_host():
    from src.core.dashboard_host import DashboardHost

    host = DashboardHost(window_title="Test Dashboard", window_icon=None)
    return host


@pytest.mark.unit
class TestPageStack:
    def test_add_page_registers_widget(self, qtbot):
        host = _make_host()
        qtbot.addWidget(host)
        page = QLabel("Page A")
        host.add_page("a", page)
        assert host._pages["a"] is page

    def test_push_page_shows_page(self, qtbot):
        host = _make_host()
        qtbot.addWidget(host)
        page_a = QLabel("A")
        page_b = QLabel("B")
        host.add_page("a", page_a)
        host.add_page("b", page_b)
        host.push_page("a")
        host.push_page("b")
        assert host._stack[-1] == "b"
        assert host._content_stack.currentWidget() is page_b

    def test_pop_page_returns_to_previous(self, qtbot):
        host = _make_host()
        qtbot.addWidget(host)
        page_a = QLabel("A")
        page_b = QLabel("B")
        host.add_page("a", page_a)
        host.add_page("b", page_b)
        host.push_page("a")
        host.push_page("b")
        host.pop_page()
        assert host._stack[-1] == "a"
        assert host._content_stack.currentWidget() is page_a

    def test_pop_page_on_single_page_is_noop(self, qtbot):
        host = _make_host()
        qtbot.addWidget(host)
        page_a = QLabel("A")
        host.add_page("a", page_a)
        host.push_page("a")
        host.pop_page()
        assert len(host._stack) == 1

    def test_back_button_hidden_on_single_page(self, qtbot):
        host = _make_host()
        qtbot.addWidget(host)
        page_a = QLabel("A")
        host.add_page("a", page_a)
        host.push_page("a")
        assert not host._back_button.isVisible()

    def test_back_button_visible_on_stack_depth_gt_1(self, qtbot):
        host = _make_host()
        qtbot.addWidget(host)
        host.add_page("a", QLabel("A"))
        host.add_page("b", QLabel("B"))
        host.push_page("a")
        host.push_page("b")
        assert not host._back_button.isHidden()

    def test_push_unknown_page_raises(self, qtbot):
        host = _make_host()
        qtbot.addWidget(host)
        with pytest.raises(KeyError):
            host.push_page("nonexistent")


@pytest.mark.unit
class TestBlurOnFocusLoss:
    def test_blur_disabled_by_default(self, qtbot):
        host = _make_host()
        qtbot.addWidget(host)
        assert host._blur_enabled is False

    def test_set_blur_on_focus_loss(self, qtbot):
        host = _make_host()
        qtbot.addWidget(host)
        host.set_blur_on_focus_loss(True)
        assert host._blur_enabled is True


@pytest.mark.unit
class TestWindowProperties:
    def test_window_title(self, qtbot):
        host = _make_host()
        qtbot.addWidget(host)
        assert host.windowTitle() == "Test Dashboard"


@pytest.mark.unit
class TestIntegrationContract:
    """Tests for build_dashboard on BaseIntegration."""

    def test_base_integration_build_dashboard_returns_none(self, tmp_path):
        from src.core.base_integration import BaseIntegration

        class StubIntegration(BaseIntegration):
            @property
            def name(self):
                return "stub"

            @property
            def display_name(self):
                return "Stub"

            async def start(self):
                pass

            async def stop(self):
                pass

        integration = StubIntegration(tmp_path, {})
        assert integration.build_dashboard() is None

    def test_integration_manager_stores_dashboard(self, tmp_path, behavior_registry, qtbot):
        from src.core.integration_manager import IntegrationManager

        manager = IntegrationManager(
            integrations_path=tmp_path,
            behavior_registry=behavior_registry,
            settings={"integrations": {}},
        )
        assert manager.get_dashboards() == {}
