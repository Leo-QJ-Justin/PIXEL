import json
from unittest.mock import MagicMock, patch

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidget

from src.ui.settings import SettingsDialog


def _make_dialog(qtbot, tmp_path, overrides=None):
    settings_file = tmp_path / "settings.json"
    data = overrides or {}
    settings_file.write_text(json.dumps(data))
    with patch("config.SETTINGS_FILE", settings_file):
        dialog = SettingsDialog()
    qtbot.addWidget(dialog)
    return dialog, settings_file


class TestNewSettingsDialog:
    def test_creates_without_error(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        assert dialog is not None

    def test_has_four_sidebar_tabs(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        sidebar = dialog.findChild(QListWidget)
        assert sidebar.count() == 4

    def test_sidebar_labels(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        sidebar = dialog.findChild(QListWidget)
        labels = [sidebar.item(i).text() for i in range(sidebar.count())]
        assert labels == ["General", "Behaviors", "Integrations", "AI & Personality"]

    def test_is_frameless(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        assert dialog.windowFlags() & Qt.WindowType.FramelessWindowHint

    def test_is_application_modal(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        assert dialog.windowModality() == Qt.WindowModality.ApplicationModal

    def test_ok_saves(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        dialog._pending["user_name"] = "Saved!"
        with patch("src.ui.settings.dialog.save_settings") as mock_save:
            dialog._on_ok()
            mock_save.assert_called_once()

    def test_ok_emits_signal(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        spy = MagicMock()
        dialog.settings_changed.connect(spy)
        with patch("src.ui.settings.dialog.save_settings"):
            dialog._on_ok()
        spy.assert_called_once()

    def test_cancel_does_not_save(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        with patch("src.ui.settings.dialog.save_settings") as mock_save:
            dialog.reject()
            mock_save.assert_not_called()
