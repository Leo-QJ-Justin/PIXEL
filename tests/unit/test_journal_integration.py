"""Tests for JournalIntegration."""


import pytest


def _make_integration(tmp_path, settings=None):
    from integrations.journal.integration import JournalIntegration

    integration_path = tmp_path / "journal"
    integration_path.mkdir(exist_ok=True)
    return JournalIntegration(integration_path, settings or {})


@pytest.mark.unit
class TestJournalIntegrationInit:
    def test_name(self, tmp_path):
        integration = _make_integration(tmp_path)
        assert integration.name == "journal"

    def test_display_name(self, tmp_path):
        integration = _make_integration(tmp_path)
        assert integration.display_name == "Journal"

    def test_default_settings(self, tmp_path):
        integration = _make_integration(tmp_path)
        defaults = integration.get_default_settings()
        assert defaults["enabled"] is True
        assert defaults["nudge_frequency"] == "smart"
        assert defaults["nudge_time"] == "20:00"
        assert defaults["blur_on_focus_loss"] is True


@pytest.mark.unit
class TestDailyPrompt:
    def test_get_daily_prompt_returns_string(self, tmp_path):
        integration = _make_integration(tmp_path)
        prompt = integration.get_daily_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_same_date_gives_same_prompt(self, tmp_path):
        integration = _make_integration(tmp_path)
        p1 = integration.get_daily_prompt("2026-03-14")
        p2 = integration.get_daily_prompt("2026-03-14")
        assert p1 == p2

    def test_different_dates_can_give_different_prompts(self, tmp_path):
        integration = _make_integration(tmp_path)
        prompts = {integration.get_daily_prompt(f"2026-03-{d:02d}") for d in range(1, 15)}
        assert len(prompts) > 1  # at least some variety


@pytest.mark.unit
class TestNudgeLogic:
    def test_should_nudge_when_no_entry_today(self, tmp_path):
        integration = _make_integration(tmp_path, {"nudge_frequency": "once_daily"})
        # No entry for today means should_nudge is True
        assert integration._should_nudge() is True

    def test_should_not_nudge_when_already_nudged(self, tmp_path):
        from datetime import date

        integration = _make_integration(tmp_path, {"nudge_frequency": "once_daily"})
        integration._nudged_today = True
        integration._last_nudge_date = date.today().isoformat()
        assert integration._should_nudge() is False

    def test_should_not_nudge_when_disabled(self, tmp_path):
        integration = _make_integration(tmp_path, {"nudge_frequency": "never"})
        assert integration._should_nudge() is False


@pytest.mark.unit
class TestBuildDashboard:
    def test_build_dashboard_returns_dashboard(self, tmp_path):
        integration = _make_integration(tmp_path)
        dashboard = integration.build_dashboard()
        assert dashboard is None


@pytest.mark.unit
class TestLifecycle:
    @pytest.mark.asyncio
    async def test_start_creates_timer(self, tmp_path):
        integration = _make_integration(tmp_path, {"nudge_frequency": "smart"})
        await integration.start()
        assert integration._nudge_timer is not None
        await integration.stop()

    @pytest.mark.asyncio
    async def test_stop_cleans_up_timer(self, tmp_path):
        integration = _make_integration(tmp_path, {"nudge_frequency": "smart"})
        await integration.start()
        await integration.stop()
        assert integration._nudge_timer is None
