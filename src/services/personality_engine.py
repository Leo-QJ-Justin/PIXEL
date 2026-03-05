"""Decorator that enriches bubble text via LLM fallback chain."""

from __future__ import annotations

import logging

from src.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are Haro, a cute robot companion that sits on the user's desktop. "
    "Rewrite the following message in Haro's voice -- cheerful, curious, "
    "and a bit childlike. "
    "Keep it to 1-2 short sentences. Don't add advice or instructions. "
    "Only output the rewritten message, nothing else."
)


class PersonalityEngine:
    """Decorator that enriches bubble text via LLM fallback chain.

    The engine is disabled by default and makes zero LLM calls unless
    the user explicitly enables it in settings. When OpenClaw is
    connected, enrichment is bypassed entirely.
    """

    def __init__(self, settings: dict):
        pe = settings.get("personality_engine", {})
        self._enabled: bool = pe.get("enabled", False)
        self._openai_key: str = pe.get("openai_api_key", "")
        self._openai_model: str = pe.get("openai_model", "gpt-4o-mini")
        self._openrouter_key: str = pe.get("openrouter_api_key", "")
        self._openrouter_model: str = pe.get("openrouter_model", "meta-llama/llama-3-8b-instruct")
        self._ollama_endpoint: str = pe.get("ollama_endpoint", "http://localhost:11434")
        self._ollama_model: str = pe.get("ollama_model", "llama3")
        self._character_prompt: str = ""
        self._openclaw_connected: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def enrich(self, text: str) -> str:
        """Enrich text via LLM fallback chain.

        Returns the original text when the engine is disabled, OpenClaw
        is connected, or both LLM sources fail.
        """
        if not self._enabled or self._openclaw_connected:
            return text

        prompt = self._character_prompt or DEFAULT_SYSTEM_PROMPT

        # Try OpenAI first (cloud)
        if self._openai_key:
            result = await LLMClient.call_openai(
                api_key=self._openai_key,
                system_prompt=prompt,
                user_text=text,
                model=self._openai_model,
            )
            if result:
                return result

        # Fallback to OpenRouter (cloud)
        if self._openrouter_key:
            result = await LLMClient.call_openrouter(
                api_key=self._openrouter_key,
                system_prompt=prompt,
                user_text=text,
                model=self._openrouter_model,
            )
            if result:
                return result

        # Fallback to Ollama (local)
        result = await LLMClient.call_ollama(
            endpoint=self._ollama_endpoint,
            system_prompt=prompt,
            user_text=text,
            model=self._ollama_model,
        )
        if result:
            return result

        # Pass-through fallback
        return text

    def set_character_prompt(self, prompt: str) -> None:
        """Update the character system prompt."""
        self._character_prompt = prompt

    def set_openclaw_connected(self, connected: bool) -> None:
        """Update OpenClaw connection status."""
        self._openclaw_connected = connected
