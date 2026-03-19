"""Platform-specific launch logic for workspace items."""

from __future__ import annotations

import logging
import subprocess
import sys
import webbrowser

logger = logging.getLogger(__name__)


class Launcher:
    """Launch apps, URLs, and folders cross-platform."""

    def launch_app(self, path: str) -> None:
        """Launch an executable."""
        try:
            subprocess.Popen([path], shell=False, start_new_session=True)
        except FileNotFoundError as err:
            raise LaunchError(f"App not found: {path}") from err
        except Exception as e:
            raise LaunchError(f"Failed to launch {path}: {e}") from e

    def launch_url(self, url: str) -> None:
        """Open URL in default browser."""
        try:
            webbrowser.open(url)
        except Exception as e:
            raise LaunchError(f"Failed to open URL {url}: {e}") from e

    def launch_folder(self, path: str) -> None:
        """Open folder in file manager."""
        try:
            if sys.platform == "win32":
                import os

                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except FileNotFoundError as err:
            raise LaunchError(f"Folder not found: {path}") from err
        except Exception as e:
            raise LaunchError(f"Failed to open folder {path}: {e}") from e

    def launch_item(self, item_type: str, path: str) -> None:
        """Launch an item by type."""
        if item_type == "app":
            self.launch_app(path)
        elif item_type == "url":
            self.launch_url(path)
        elif item_type == "folder":
            self.launch_folder(path)
        else:
            raise LaunchError(f"Unknown item type: {item_type}")


class LaunchError(Exception):
    pass
