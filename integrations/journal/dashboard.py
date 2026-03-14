"""Journal dashboard — wires stats surface, vault list, and entry editor."""

from __future__ import annotations

from integrations.journal.widgets.entry_editor import EntryEditor
from integrations.journal.widgets.stats_surface import StatsSurface
from integrations.journal.widgets.vault_list import VaultList
from src.core.dashboard_host import DashboardHost


class JournalDashboard(DashboardHost):
    """Journal dashboard with stats → vault → editor navigation."""

    def __init__(self, integration) -> None:
        super().__init__(window_title="Journal", window_icon=None)
        self._integration = integration
        self._store = integration._get_store()

        blur = integration.settings.get("blur_on_focus_loss", True)
        self.set_blur_on_focus_loss(blur)

        self.setMinimumSize(500, 600)
        self.resize(550, 700)

        self._build_pages()

    def _build_pages(self) -> None:
        # Stats surface (default)
        self._stats = StatsSurface(self._integration)
        self._stats.open_vault_clicked.connect(self._open_vault)
        self._stats.write_prompt_clicked.connect(self._open_guided_entry)
        self._stats.date_clicked.connect(self._open_entry_for_date)
        self.add_page("stats", self._stats)

        # Vault list
        self._vault = VaultList(self._store)
        self._vault.entry_clicked.connect(self._open_entry_for_date)
        self._vault.new_entry_clicked.connect(self._open_new_entry)
        self.add_page("vault", self._vault)

        # Entry editor
        self._editor = EntryEditor(self._integration)
        self._editor.entry_saved.connect(self._on_entry_saved)
        self.add_page("editor", self._editor)

        # Start on stats
        self.push_page("stats")

    def _open_vault(self) -> None:
        self._vault.refresh()
        self.push_page("vault")

    def _open_new_entry(self) -> None:
        self._editor.open_new_entry()
        self.push_page("editor")

    def _open_guided_entry(self, prompt: str) -> None:
        self._editor.open_new_entry(mode="guided", prompt=prompt)
        self.push_page("editor")

    def _open_entry_for_date(self, date_str: str) -> None:
        self._editor.open_existing_entry(date_str)
        self.push_page("editor")

    def _on_entry_saved(self, date_str: str, mood: str) -> None:
        # Trigger pet reactions on save
        self._integration.on_entry_saved(mood if mood else None)
        # Refresh stats when coming back
        self._stats.refresh()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._stats.refresh()
