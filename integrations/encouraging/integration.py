"""Encouraging messages integration — periodic motivational nudges."""

from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QTimer

from src.core.base_integration import BaseIntegration

logger = logging.getLogger(__name__)

# Message templates per trigger type.
# The personality engine will rewrite these in PIXEL's voice.
MESSAGES: dict[str, list[str]] = {
    "restless": [
        "You've been going for a while — maybe stretch your legs?",
        "Long session! A quick break can help you recharge.",
        "Your focus is impressive, but don't forget to rest!",
        "Been at it for a while — how about a water break?",
        "Even machines need a cooldown cycle sometimes!",
    ],
    "proud": [
        "Look at that streak — you're on a roll!",
        "Consistency is your superpower right now!",
        "Your habits are really coming together!",
        "Streak keeper! That dedication is paying off.",
        "You haven't missed a beat — impressive!",
    ],
    "excited": [
        "Welcome back! Ready to get things done?",
        "You're back! I missed you!",
        "Good to see you again!",
        "Hey, welcome back to the desk!",
        "Back in action! Let's go!",
    ],
    "observant": [
        "I see you working hard over there!",
        "Looks like you're in the zone!",
        "You're really locked in today!",
        "Heads-down mode activated!",
        "Productive vibes detected!",
    ],
    "curious": [
        "Did you know short breaks boost creativity?",
        "I wonder what you're working on!",
        "Fun fact: your brain consolidates learning during rest.",
        "What's on the agenda today?",
        "Remember to celebrate small wins!",
    ],
    "impressed": [
        "Another milestone — you're collecting them!",
        "Look how far you've come!",
        "The consistency is adding up — well done!",
        "Milestone reached! Keep it going!",
        "That's a lot of check marks!",
    ],
}


class EncouragingIntegration(BaseIntegration):
    """Periodic motivational messages based on user activity."""

    def __init__(self, integration_path: Path, settings: dict[str, Any]) -> None:
        super().__init__(integration_path, settings)
        self._eval_timer: QTimer | None = None
        self._cooldown_until: datetime = datetime.min
        self._manager = None
        self._pet_widget = None

        # State tracking
        self._last_was_idle = False  # For "excited" trigger (user returned)
        self._last_milestone_count: dict[str, int] = {}  # habit_id -> last total
        self._restless_reminded = False  # One reminder per continuous session
        self._proud_notified: dict[str, int] = {}  # habit_id -> streak when last notified

    @property
    def name(self) -> str:
        return "encouraging"

    @property
    def display_name(self) -> str:
        return "Encouraging Messages"

    def get_default_settings(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "cooldown_min_minutes": 30,
            "cooldown_max_minutes": 60,
            "evaluation_interval_seconds": 30,
            "triggers": {
                "restless": {"enabled": True, "threshold_minutes": 90},
                "observant": {"enabled": True},
                "excited": {"enabled": True, "idle_threshold_minutes": 15},
                "proud": {"enabled": True, "streak_threshold": 3},
                "curious": {"enabled": True},
                "impressed": {"enabled": True, "milestone_interval": 10},
            },
        }

    def set_manager(self, manager) -> None:
        self._manager = manager

    def setup_ui(self, pet_widget) -> None:
        self._pet_widget = pet_widget

    async def start(self) -> None:
        interval_s = self._settings.get("evaluation_interval_seconds", 30)
        self._eval_timer = QTimer()
        self._eval_timer.timeout.connect(self._on_eval_tick)
        self._eval_timer.start(interval_s * 1000)
        logger.info(
            f"Encouraging messages started (interval={interval_s}s, "
            f"cooldown={self._settings.get('cooldown_min_minutes', 30)}-"
            f"{self._settings.get('cooldown_max_minutes', 60)}min)"
        )

    async def stop(self) -> None:
        if self._eval_timer:
            self._eval_timer.stop()
            self._eval_timer = None
        logger.info("Encouraging messages stopped")

    # ------------------------------------------------------------------
    # Evaluation loop
    # ------------------------------------------------------------------

    def _on_eval_tick(self) -> None:
        """Called every evaluation_interval_seconds."""
        # Cooldown check
        if datetime.now() < self._cooldown_until:
            return

        triggered = self._evaluate_triggers()
        if not triggered:
            return

        trigger_name, message = triggered
        context = {"bubble_text": message, "bubble_duration_ms": 6000}

        # If pet is sleeping, wake it up with a wave to deliver the message
        pet_sleeping = False
        if self._pet_widget:
            from src.core.pet_state import PetState
            pet_sleeping = self._pet_widget._state_machine.state == PetState.SLEEPING

        if pet_sleeping:
            self.trigger("wave", context)
        else:
            self.notify(context)

        logger.info(f"Encouraging message sent (trigger={trigger_name}, woke_pet={pet_sleeping})")

        # Set random cooldown
        cd_min = self._settings.get("cooldown_min_minutes", 30)
        cd_max = self._settings.get("cooldown_max_minutes", 60)
        cooldown = random.randint(cd_min, max(cd_min, cd_max))
        self._cooldown_until = datetime.now() + timedelta(minutes=cooldown)

    def _evaluate_triggers(self) -> tuple[str, str] | None:
        """Check all enabled triggers in priority order. Returns (name, message) or None."""
        triggers = self._settings.get("triggers", {})

        # Priority order: restless > proud > excited > impressed > observant > curious
        checks = [
            ("restless", self._check_restless),
            ("proud", self._check_proud),
            ("excited", self._check_excited),
            ("impressed", self._check_impressed),
            ("observant", self._check_observant),
            ("curious", self._check_curious),
        ]

        for name, check_fn in checks:
            trigger_cfg = triggers.get(name, {})
            if not trigger_cfg.get("enabled", True):
                continue
            if check_fn(trigger_cfg):
                return (name, random.choice(MESSAGES[name]))

        return None

    # ------------------------------------------------------------------
    # Individual trigger checks
    # ------------------------------------------------------------------

    def _check_restless(self, cfg: dict) -> bool:
        """User has been active continuously for too long."""
        if not self._manager:
            return False
        st = self._manager.get_integration("screen_time")
        if not st:
            return False
        threshold_s = cfg.get("threshold_minutes", 90) * 60
        if st.continuous_active_seconds >= threshold_s and not self._restless_reminded:
            self._restless_reminded = True
            return True
        if st.continuous_active_seconds < 60:
            # Reset when user takes a break
            self._restless_reminded = False
        return False

    def _check_proud(self, cfg: dict) -> bool:
        """Any habit has a streak above threshold (fires once per new streak level)."""
        if not self._manager:
            return False
        habits = self._manager.get_integration("habits")
        if not habits:
            return False
        try:
            store = habits.get_store()
            threshold = cfg.get("streak_threshold", 3)
            for h in store.list_habits():
                hid = h["id"]
                streak = store.get_streak(hid)
                last_notified = self._proud_notified.get(hid, 0)
                if streak >= threshold and streak > last_notified:
                    self._proud_notified[hid] = streak
                    return True
        except Exception:
            logger.debug("Could not check habit streaks", exc_info=True)
        return False

    def _check_excited(self, cfg: dict) -> bool:
        """User just returned after being idle."""
        if not self._manager:
            return False
        st = self._manager.get_integration("screen_time")
        if not st:
            return False
        # Screen time polls every 5s, so after an idle reset _continuous_active_s
        # jumps from 0 to 5 on the first active tick. Use <= 10 to catch it.
        is_idle = st.continuous_active_seconds <= 10
        was_idle = self._last_was_idle
        self._last_was_idle = is_idle
        # Fire only when transitioning from idle to active
        if was_idle and not is_idle:
            return True
        return False

    def _check_impressed(self, cfg: dict) -> bool:
        """Total habit completions hit a milestone interval."""
        if not self._manager:
            return False
        habits = self._manager.get_integration("habits")
        if not habits:
            return False
        try:
            store = habits.get_store()
            interval = cfg.get("milestone_interval", 10)
            for h in store.list_habits():
                hid = h["id"]
                total = store.get_total_completions(hid)
                last = self._last_milestone_count.get(hid, total)
                self._last_milestone_count[hid] = total
                if total > 0 and total != last and total % interval == 0:
                    return True
        except Exception:
            logger.debug("Could not check habit milestones", exc_info=True)
        return False

    def _check_observant(self, _cfg: dict) -> bool:
        """Random chance when user is actively working."""
        if not self._manager:
            return False
        st = self._manager.get_integration("screen_time")
        if not st:
            return False
        # Only fire if user has been active for at least 5 minutes
        if st.continuous_active_seconds < 300:
            return False
        return random.random() < 0.05  # ~5% chance per tick

    def _check_curious(self, _cfg: dict) -> bool:
        """Low random chance — fun facts and general encouragement."""
        return random.random() < 0.03  # ~3% chance per tick
