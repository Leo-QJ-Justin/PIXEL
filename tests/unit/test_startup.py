"""Tests for cross-platform startup utility."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestGetLaunchCommand:
    """Tests for _get_launch_command."""

    def test_returns_python_and_main_py(self, monkeypatch):
        monkeypatch.setattr("sys.executable", "/usr/bin/python3")
        monkeypatch.setattr("sys.platform", "linux")

        from src.utils.startup import _get_launch_command

        cmd = _get_launch_command()
        assert cmd[0] == "/usr/bin/python3"
        assert cmd[1].endswith("main.py")

    def test_windows_prefers_pythonw(self, monkeypatch, tmp_path):
        pythonw = tmp_path / "pythonw.exe"
        pythonw.touch()
        python = tmp_path / "python.exe"
        python.touch()

        monkeypatch.setattr("sys.executable", str(python))
        monkeypatch.setattr("sys.platform", "win32")

        from src.utils.startup import _get_launch_command

        cmd = _get_launch_command()
        assert cmd[0] == str(pythonw)

    def test_windows_falls_back_to_python(self, monkeypatch, tmp_path):
        python = tmp_path / "python.exe"
        python.touch()
        # pythonw.exe does NOT exist

        monkeypatch.setattr("sys.executable", str(python))
        monkeypatch.setattr("sys.platform", "win32")

        from src.utils.startup import _get_launch_command

        cmd = _get_launch_command()
        assert cmd[0] == str(python)


@pytest.mark.unit
class TestWindows:
    """Tests for Windows registry startup."""

    def test_enable_sets_registry_value(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "win32")

        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = 0x80000001
        mock_winreg.KEY_SET_VALUE = 0x0002
        mock_winreg.REG_SZ = 1

        with patch.dict("sys.modules", {"winreg": mock_winreg}):
            import importlib

            from src.utils import startup

            importlib.reload(startup)
            startup.set_startup_enabled(True)

        mock_winreg.SetValueEx.assert_called_once()
        args = mock_winreg.SetValueEx.call_args
        assert args[0][0] == mock_key
        assert args[0][1] == "PixelDesktopPet"
        mock_winreg.CloseKey.assert_called_once_with(mock_key)

    def test_disable_deletes_registry_value(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "win32")

        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = 0x80000001
        mock_winreg.KEY_SET_VALUE = 0x0002

        with patch.dict("sys.modules", {"winreg": mock_winreg}):
            import importlib

            from src.utils import startup

            importlib.reload(startup)
            startup.set_startup_enabled(False)

        mock_winreg.DeleteValue.assert_called_once_with(mock_key, "PixelDesktopPet")
        mock_winreg.CloseKey.assert_called_once_with(mock_key)

    def test_check_returns_true_when_key_exists(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "win32")

        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = 0x80000001
        mock_winreg.KEY_READ = 0x20019
        mock_winreg.QueryValueEx.return_value = ("some_path", 1)

        with patch.dict("sys.modules", {"winreg": mock_winreg}):
            import importlib

            from src.utils import startup

            importlib.reload(startup)
            assert startup.is_startup_enabled() is True

    def test_check_returns_false_when_key_missing(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "win32")

        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = 0x80000001
        mock_winreg.KEY_READ = 0x20019
        mock_winreg.QueryValueEx.side_effect = FileNotFoundError

        with patch.dict("sys.modules", {"winreg": mock_winreg}):
            import importlib

            from src.utils import startup

            importlib.reload(startup)
            assert startup.is_startup_enabled() is False


@pytest.mark.unit
class TestMacOS:
    """Tests for macOS LaunchAgent startup."""

    def test_enable_creates_plist(self, monkeypatch, tmp_path):
        monkeypatch.setattr("sys.platform", "darwin")

        plist_path = tmp_path / "com.pixel.desktop-pet.plist"
        monkeypatch.setattr("src.utils.startup._MACOS_PLIST_PATH", plist_path)

        import importlib

        from src.utils import startup

        importlib.reload(startup)
        startup._MACOS_PLIST_PATH = plist_path
        startup.set_startup_enabled(True)

        assert plist_path.exists()
        import plistlib

        with open(plist_path, "rb") as f:
            data = plistlib.load(f)
        assert data["Label"] == "com.pixel.desktop-pet"
        assert data["RunAtLoad"] is True
        assert len(data["ProgramArguments"]) == 2

    def test_disable_removes_plist(self, monkeypatch, tmp_path):
        monkeypatch.setattr("sys.platform", "darwin")

        plist_path = tmp_path / "com.pixel.desktop-pet.plist"
        plist_path.touch()

        import importlib

        from src.utils import startup

        importlib.reload(startup)
        startup._MACOS_PLIST_PATH = plist_path
        startup.set_startup_enabled(False)

        assert not plist_path.exists()

    def test_check_returns_true_when_plist_exists(self, monkeypatch, tmp_path):
        monkeypatch.setattr("sys.platform", "darwin")

        plist_path = tmp_path / "com.pixel.desktop-pet.plist"
        plist_path.touch()

        import importlib

        from src.utils import startup

        importlib.reload(startup)
        startup._MACOS_PLIST_PATH = plist_path

        assert startup.is_startup_enabled() is True

    def test_check_returns_false_when_no_plist(self, monkeypatch, tmp_path):
        monkeypatch.setattr("sys.platform", "darwin")

        plist_path = tmp_path / "com.pixel.desktop-pet.plist"

        import importlib

        from src.utils import startup

        importlib.reload(startup)
        startup._MACOS_PLIST_PATH = plist_path

        assert startup.is_startup_enabled() is False


@pytest.mark.unit
class TestLinux:
    """Tests for Linux XDG autostart."""

    def test_enable_creates_desktop_file(self, monkeypatch, tmp_path):
        monkeypatch.setattr("sys.platform", "linux")

        desktop_path = tmp_path / "haro-desktop-pet.desktop"
        monkeypatch.setattr("src.utils.startup._LINUX_DESKTOP_PATH", desktop_path)

        import importlib

        from src.utils import startup

        importlib.reload(startup)
        startup._LINUX_DESKTOP_PATH = desktop_path
        startup.set_startup_enabled(True)

        assert desktop_path.exists()
        content = desktop_path.read_text()
        assert "[Desktop Entry]" in content
        assert "Type=Application" in content
        assert "X-GNOME-Autostart-enabled=true" in content
        assert "PixelDesktopPet" in content

    def test_disable_removes_desktop_file(self, monkeypatch, tmp_path):
        monkeypatch.setattr("sys.platform", "linux")

        desktop_path = tmp_path / "haro-desktop-pet.desktop"
        desktop_path.touch()

        import importlib

        from src.utils import startup

        importlib.reload(startup)
        startup._LINUX_DESKTOP_PATH = desktop_path
        startup.set_startup_enabled(False)

        assert not desktop_path.exists()

    def test_check_returns_true_when_desktop_exists(self, monkeypatch, tmp_path):
        monkeypatch.setattr("sys.platform", "linux")

        desktop_path = tmp_path / "haro-desktop-pet.desktop"
        desktop_path.touch()

        import importlib

        from src.utils import startup

        importlib.reload(startup)
        startup._LINUX_DESKTOP_PATH = desktop_path

        assert startup.is_startup_enabled() is True

    def test_check_returns_false_when_no_desktop(self, monkeypatch, tmp_path):
        monkeypatch.setattr("sys.platform", "linux")

        desktop_path = tmp_path / "haro-desktop-pet.desktop"

        import importlib

        from src.utils import startup

        importlib.reload(startup)
        startup._LINUX_DESKTOP_PATH = desktop_path

        assert startup.is_startup_enabled() is False


@pytest.mark.unit
class TestErrorHandling:
    """Tests for graceful error handling."""

    def test_set_startup_logs_error_on_failure(self, monkeypatch, caplog):
        import logging

        monkeypatch.setattr("sys.platform", "linux")

        import importlib

        from src.utils import startup

        importlib.reload(startup)

        with caplog.at_level(logging.ERROR, logger="src.utils.startup"):
            with patch.object(startup, "_set_linux", side_effect=OSError("disk full")):
                startup.set_startup_enabled(True)

        assert "Failed to enable startup" in caplog.text

    def test_is_startup_enabled_returns_false_on_error(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "win32")

        mock_winreg = MagicMock()
        mock_winreg.OpenKey.side_effect = OSError("access denied")
        mock_winreg.HKEY_CURRENT_USER = 0x80000001
        mock_winreg.KEY_READ = 0x20019

        with patch.dict("sys.modules", {"winreg": mock_winreg}):
            import importlib

            from src.utils import startup

            importlib.reload(startup)
            assert startup.is_startup_enabled() is False
