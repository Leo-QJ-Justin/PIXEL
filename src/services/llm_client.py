"""LLM client for personality enrichment via OpenRouter and Ollama."""

from __future__ import annotations

import logging

import aiohttp

logger = logging.getLogger(__name__)

# Short timeout to avoid blocking the desktop pet UI
_TIMEOUT = aiohttp.ClientTimeout(total=5)


class LLMClient:
    """Handles LLM API calls for personality enrichment."""

    @staticmethod
    async def call_openrouter(
        api_key: str,
        system_prompt: str,
        user_text: str,
        model: str = "meta-llama/llama-3-8b-instruct",
    ) -> str | None:
        """Call OpenRouter API. Returns enriched text or None on failure."""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            "max_tokens": 150,
        }

        try:
            async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        logger.warning("OpenRouter returned status %d", resp.status)
                        return None
                    data = await resp.json()
                    choices = data.get("choices", [])
                    if not choices:
                        return None
                    content = choices[0].get("message", {}).get("content", "")
                    return content.strip() or None
        except Exception:
            logger.debug("OpenRouter call failed", exc_info=True)
            return None

    @staticmethod
    async def call_openai(
        api_key: str,
        system_prompt: str,
        user_text: str,
        model: str = "gpt-4o-mini",
    ) -> str | None:
        """Call OpenAI API. Returns enriched text or None on failure."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            "max_tokens": 150,
        }

        try:
            async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        logger.warning("OpenAI returned status %d", resp.status)
                        return None
                    data = await resp.json()
                    choices = data.get("choices", [])
                    if not choices:
                        return None
                    content = choices[0].get("message", {}).get("content", "")
                    return content.strip() or None
        except Exception:
            logger.debug("OpenAI call failed", exc_info=True)
            return None

    @staticmethod
    async def call_ollama(
        endpoint: str,
        system_prompt: str,
        user_text: str,
        model: str = "llama3",
    ) -> str | None:
        """Call Ollama API. Returns enriched text or None on failure."""
        url = f"{endpoint.rstrip('/')}/api/generate"
        payload = {
            "model": model,
            "system": system_prompt,
            "prompt": user_text,
            "stream": False,
        }

        try:
            async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        logger.warning("Ollama returned status %d", resp.status)
                        return None
                    data = await resp.json()
                    response_text = data.get("response", "")
                    return response_text.strip() or None
        except Exception:
            logger.debug("Ollama call failed", exc_info=True)
            return None
