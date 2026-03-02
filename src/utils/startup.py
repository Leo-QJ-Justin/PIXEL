"""Cross-platform auto-start on login utility."""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

APP_NAME = "HaroDesktopPet"
_MAIN_PY = Path(__file__).resolve().parent.parent.parent / "main.py"


def _get_launch_command() -> list[str]:
    """Return the command list to launch the app."""
    python = sys.executable
    # On Windows, prefer pythonw.exe to suppress the console window
    if sys.platform == "win32":
        pythonw = Path(python).with_name("pythonw.exe")
        if pythonw.exists():
            python = str(pythonw)
    return [python, str(_MAIN_PY)]


def set_startup_enabled(enabled: bool) -> None:
    """Enable or disable auto-start on login for the current platform."""
    try:
        if sys.platform == "win32":
            _set_windows(enabled)
        elif sys.platform == "darwin":
            _set_macos(enabled)
        else:
            _set_linux(enabled)
    except Exception:
        logger.exception("Failed to %s startup", "enable" if enabled else "disable")


def is_startup_enabled() -> bool:
    """Check whether auto-start is currently configured."""
    try:
        if sys.platform == "win32":
            return _check_windows()
        elif sys.platform == "darwin":
            return _check_macos()
        else:
            return _check_linux()
    except Exception:
        logger.exception("Failed to check startup status")
        return False


# ---------------------------------------------------------------------------
# Windows — Registry
# ---------------------------------------------------------------------------

_WIN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _set_windows(enabled: bool) -> None:
    import winreg

    cmd = _get_launch_command()
    value = f'"{cmd[0]}" "{cmd[1]}"'

    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _WIN_KEY_PATH, 0, winreg.KEY_SET_VALUE)
    try:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, value)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)


def _check_windows() -> bool:
    import winreg

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _WIN_KEY_PATH, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except OSError:
        return False


# ---------------------------------------------------------------------------
# macOS — LaunchAgent plist
# ---------------------------------------------------------------------------

_MACOS_PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / "com.haro.desktop-pet.plist"


def _set_macos(enabled: bool) -> None:
    if enabled:
        import plistlib

        cmd = _get_launch_command()
        plist = {
            "Label": "com.haro.desktop-pet",
            "ProgramArguments": cmd,
            "RunAtLoad": True,
        }
        _MACOS_PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_MACOS_PLIST_PATH, "wb") as f:
            plistlib.dump(plist, f)
    else:
        _MACOS_PLIST_PATH.unlink(missing_ok=True)


def _check_macos() -> bool:
    return _MACOS_PLIST_PATH.exists()


# ---------------------------------------------------------------------------
# Linux — XDG autostart .desktop file
# ---------------------------------------------------------------------------

_LINUX_DESKTOP_PATH = Path.home() / ".config" / "autostart" / "haro-desktop-pet.desktop"


def _set_linux(enabled: bool) -> None:
    if enabled:
        cmd = _get_launch_command()
        content = (
            "[Desktop Entry]\n"
            f"Name={APP_NAME}\n"
            "Type=Application\n"
            f'Exec="{cmd[0]}" "{cmd[1]}"\n'
            "X-GNOME-Autostart-enabled=true\n"
        )
        _LINUX_DESKTOP_PATH.parent.mkdir(parents=True, exist_ok=True)
        _LINUX_DESKTOP_PATH.write_text(content)
    else:
        _LINUX_DESKTOP_PATH.unlink(missing_ok=True)


def _check_linux() -> bool:
    return _LINUX_DESKTOP_PATH.exists()
