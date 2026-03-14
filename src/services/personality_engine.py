"""Personality engine — enriches bubble text via LiteLLM."""

from __future__ import annotations

import logging
import os

import litellm

logger = logging.getLogger(__name__)

# Suppress litellm's noisy default logging
if hasattr(litellm, "suppress_debug_info"):
    litellm.suppress_debug_info = True

DEFAULT_SYSTEM_PROMPT = (
    "You are PIXEL, a cute robot companion that sits on the user's desktop. "
    "Rewrite the following message in PIXEL's voice -- cheerful, curious, "
    "and a bit childlike. "
    "Keep it to 1-2 short sentences. Don't add advice or instructions. "
    "Only output the rewritten message, nothing else."
)

PROVIDER_CONFIG: dict[str, dict] = {
    "openai": {
        "prefix": "",
        "default_model": "gpt-4o-mini",
        "needs_api_key": True,
        "needs_endpoint": False,
    },
    "anthropic": {
        "prefix": "anthropic/",
        "default_model": "claude-haiku-4-5-20251001",
        "needs_api_key": True,
        "needs_endpoint": False,
    },
    "openrouter": {
        "prefix": "openrouter/",
        "default_model": "meta-llama/llama-3-8b-instruct",
        "needs_api_key": True,
        "needs_endpoint": False,
    },
    "groq": {
        "prefix": "groq/",
        "default_model": "llama3-8b-8192",
        "needs_api_key": True,
        "needs_endpoint": False,
    },
    "mistral": {
        "prefix": "mistral/",
        "default_model": "mistral-small-latest",
        "needs_api_key": True,
        "needs_endpoint": False,
    },
    "google_gemini": {
        "prefix": "gemini/",
        "default_model": "gemini-2.0-flash",
        "needs_api_key": True,
        "needs_endpoint": False,
    },
    "together_ai": {
        "prefix": "together_ai/",
        "default_model": "meta-llama/Meta-Llama-3-8B-Instruct-Turbo",
        "needs_api_key": True,
        "needs_endpoint": False,
    },
    "deepseek": {
        "prefix": "deepseek/",
        "default_model": "deepseek-chat",
        "needs_api_key": True,
        "needs_endpoint": False,
    },
    "ollama": {
        "prefix": "ollama/",
        "default_model": "llama3",
        "needs_api_key": False,
        "needs_endpoint": True,
    },
    "custom": {
        "prefix": "",
        "default_model": "",
        "needs_api_key": True,
        "needs_endpoint": True,
    },
}


class PersonalityEngine:
    """Enriches bubble text via LiteLLM."""

    def __init__(self, settings: dict) -> None:
        self._character_prompt: str = ""
        self._openclaw_connected: bool = False
        self._load_settings(settings)

    def _load_settings(self, settings: dict) -> None:
        pe = settings.get("personality_engine", {})
        self._enabled: bool = pe.get("enabled", False)
        self._provider: str = pe.get("provider", "openai")
        self._model: str = pe.get("model", "gpt-4o-mini")
        self._api_key: str = os.environ.get("LLM_API_KEY") or pe.get("api_key", "")
        self._endpoint: str = os.environ.get("LLM_ENDPOINT") or pe.get("endpoint", "")

    def _build_model_string(self) -> str:
        cfg = PROVIDER_CONFIG.get(self._provider, PROVIDER_CONFIG["custom"])
        return f"{cfg['prefix']}{self._model}"

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def enrich(self, text: str) -> str:
        """Enrich text via LLM. Returns original on failure or when disabled."""
        if not self._enabled or self._openclaw_connected:
            return text

        prompt = self._character_prompt or DEFAULT_SYSTEM_PROMPT

        try:
            kwargs: dict = {
                "model": self._build_model_string(),
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text},
                ],
                "max_tokens": 150,
                "temperature": 0.7,
                "timeout": 8,
            }

            cfg = PROVIDER_CONFIG.get(self._provider, {})
            if cfg.get("needs_api_key") and self._api_key:
                kwargs["api_key"] = self._api_key
            if cfg.get("needs_endpoint") and self._endpoint:
                kwargs["api_base"] = self._endpoint

            response = await litellm.acompletion(**kwargs)
            content = response.choices[0].message.content
            return content.strip() if content else text
        except Exception:
            logger.debug("LLM enrichment failed", exc_info=True)
            return text

    def update_settings(self, settings: dict) -> None:
        """Reload settings (called when user saves Settings dialog)."""
        self._load_settings(settings)

    def set_character_prompt(self, prompt: str) -> None:
        self._character_prompt = prompt

    def set_openclaw_connected(self, connected: bool) -> None:
        self._openclaw_connected = connected
