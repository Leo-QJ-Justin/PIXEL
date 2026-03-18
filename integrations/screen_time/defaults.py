"""Default app category mappings per platform."""

from __future__ import annotations

import sys

PRODUCTIVE = "Productive"
NEUTRAL = "Neutral"
DISTRACTING = "Distracting"

_WINDOWS_DEFAULTS = {
    "Code.exe": (PRODUCTIVE, "VS Code"),
    "devenv.exe": (PRODUCTIVE, "Visual Studio"),
    "idea64.exe": (PRODUCTIVE, "IntelliJ IDEA"),
    "pycharm64.exe": (PRODUCTIVE, "PyCharm"),
    "WindowsTerminal.exe": (PRODUCTIVE, "Windows Terminal"),
    "cmd.exe": (PRODUCTIVE, "Command Prompt"),
    "powershell.exe": (PRODUCTIVE, "PowerShell"),
    "pwsh.exe": (PRODUCTIVE, "PowerShell"),
    "notepad++.exe": (PRODUCTIVE, "Notepad++"),
    "sublime_text.exe": (PRODUCTIVE, "Sublime Text"),
    "Figma.exe": (PRODUCTIVE, "Figma"),
    "Notion.exe": (PRODUCTIVE, "Notion"),
    "Obsidian.exe": (PRODUCTIVE, "Obsidian"),
    "WINWORD.EXE": (PRODUCTIVE, "Word"),
    "EXCEL.EXE": (PRODUCTIVE, "Excel"),
    "POWERPNT.EXE": (PRODUCTIVE, "PowerPoint"),
    "chrome.exe": (NEUTRAL, "Chrome"),
    "firefox.exe": (NEUTRAL, "Firefox"),
    "msedge.exe": (NEUTRAL, "Edge"),
    "brave.exe": (NEUTRAL, "Brave"),
    "explorer.exe": (NEUTRAL, "File Explorer"),
    "Discord.exe": (DISTRACTING, "Discord"),
    "Slack.exe": (DISTRACTING, "Slack"),
    "Telegram.exe": (DISTRACTING, "Telegram"),
    "WhatsApp.exe": (DISTRACTING, "WhatsApp"),
    "Steam.exe": (DISTRACTING, "Steam"),
    "EpicGamesLauncher.exe": (DISTRACTING, "Epic Games"),
    "spotify.exe": (NEUTRAL, "Spotify"),
}

_MACOS_DEFAULTS = {
    "com.microsoft.VSCode": (PRODUCTIVE, "VS Code"),
    "com.apple.Terminal": (PRODUCTIVE, "Terminal"),
    "com.googlecode.iterm2": (PRODUCTIVE, "iTerm2"),
    "com.figma.Desktop": (PRODUCTIVE, "Figma"),
    "notion.id": (PRODUCTIVE, "Notion"),
    "md.obsidian": (PRODUCTIVE, "Obsidian"),
    "com.microsoft.Word": (PRODUCTIVE, "Word"),
    "com.microsoft.Excel": (PRODUCTIVE, "Excel"),
    "com.google.Chrome": (NEUTRAL, "Chrome"),
    "org.mozilla.firefox": (NEUTRAL, "Firefox"),
    "com.apple.Safari": (NEUTRAL, "Safari"),
    "com.apple.finder": (NEUTRAL, "Finder"),
    "com.apple.Preview": (NEUTRAL, "Preview"),
    "com.hnc.Discord": (DISTRACTING, "Discord"),
    "com.tinyspeck.slackmacgap": (DISTRACTING, "Slack"),
    "ru.keepcoder.Telegram": (DISTRACTING, "Telegram"),
    "com.valvesoftware.steam": (DISTRACTING, "Steam"),
    "com.spotify.client": (NEUTRAL, "Spotify"),
}

_LINUX_DEFAULTS = {
    "code": (PRODUCTIVE, "VS Code"),
    "vim": (PRODUCTIVE, "Vim"),
    "nvim": (PRODUCTIVE, "Neovim"),
    "emacs": (PRODUCTIVE, "Emacs"),
    "gnome-terminal": (PRODUCTIVE, "Terminal"),
    "konsole": (PRODUCTIVE, "Terminal"),
    "alacritty": (PRODUCTIVE, "Alacritty"),
    "kitty": (PRODUCTIVE, "Kitty"),
    "figma-linux": (PRODUCTIVE, "Figma"),
    "notion-app": (PRODUCTIVE, "Notion"),
    "obsidian": (PRODUCTIVE, "Obsidian"),
    "google-chrome": (NEUTRAL, "Chrome"),
    "firefox": (NEUTRAL, "Firefox"),
    "brave-browser": (NEUTRAL, "Brave"),
    "nautilus": (NEUTRAL, "Files"),
    "thunar": (NEUTRAL, "Files"),
    "Discord": (DISTRACTING, "Discord"),
    "slack": (DISTRACTING, "Slack"),
    "telegram-desktop": (DISTRACTING, "Telegram"),
    "steam": (DISTRACTING, "Steam"),
    "spotify": (NEUTRAL, "Spotify"),
}


def get_default_categories() -> dict[str, tuple[str, str]]:
    """Return default (category, display_name) mapping for the current platform."""
    if sys.platform == "win32":
        return dict(_WINDOWS_DEFAULTS)
    elif sys.platform == "darwin":
        return dict(_MACOS_DEFAULTS)
    else:
        return dict(_LINUX_DEFAULTS)
