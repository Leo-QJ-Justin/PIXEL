"""Tests for PersonalityEngine with LiteLLM backend."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest

import config
from src.services.personality_engine import PROVIDER_CONFIG, PersonalityEngine


class TestPersonalityEngineDefaults:
    def test_default_settings_has_provider_field(self):
        pe = config.DEFAULT_SETTINGS["personality_engine"]
        assert pe["provider"] == "openai"

    def test_default_settings_has_model_field(self):
        pe = config.DEFAULT_SETTINGS["personality_engine"]
        assert pe["model"] == "gpt-4o-mini"

    def test_default_settings_has_api_key_field(self):
        pe = config.DEFAULT_SETTINGS["personality_engine"]
        assert pe["api_key"] == ""

    def test_default_settings_has_endpoint_field(self):
        pe = config.DEFAULT_SETTINGS["personality_engine"]
        assert pe["endpoint"] == ""

    def test_default_settings_no_old_provider_keys(self):
        pe = config.DEFAULT_SETTINGS["personality_engine"]
        assert "openai_api_key" not in pe
        assert "openrouter_api_key" not in pe
        assert "ollama_endpoint" not in pe


class TestProviderConfig:
    ALL_PROVIDERS = [
        "openai",
        "anthropic",
        "openrouter",
        "groq",
        "mistral",
        "google_gemini",
        "together_ai",
        "deepseek",
        "ollama",
        "custom",
    ]

    def test_has_all_10_providers(self):
        for provider in self.ALL_PROVIDERS:
            assert provider in PROVIDER_CONFIG, f"Missing provider: {provider}"

    def test_openai_prefix_is_empty(self):
        assert PROVIDER_CONFIG["openai"]["prefix"] == ""

    def test_anthropic_prefix(self):
        assert PROVIDER_CONFIG["anthropic"]["prefix"] == "anthropic/"

    def test_ollama_needs_api_key_false(self):
        assert PROVIDER_CONFIG["ollama"]["needs_api_key"] is False

    def test_ollama_needs_endpoint_true(self):
        assert PROVIDER_CONFIG["ollama"]["needs_endpoint"] is True

    def test_every_provider_has_default_model(self):
        for provider in self.ALL_PROVIDERS:
            assert "default_model" in PROVIDER_CONFIG[provider], (
                f"Provider {provider} missing default_model"
            )


class TestPersonalityEngineInit:
    def test_disabled_by_default_with_empty_settings(self):
        engine = PersonalityEngine({})
        assert engine._enabled is False

    def test_reads_provider_and_model_from_settings(self):
        settings = {
            "personality_engine": {"provider": "anthropic", "model": "claude-haiku-4-5-20251001"}
        }
        engine = PersonalityEngine(settings)
        assert engine._provider == "anthropic"
        assert engine._model == "claude-haiku-4-5-20251001"

    def test_env_var_overrides_api_key(self):
        settings = {"personality_engine": {"api_key": "settings-key"}}
        with patch.dict(os.environ, {"LLM_API_KEY": "env-key"}):
            engine = PersonalityEngine(settings)
        assert engine._api_key == "env-key"

    def test_env_var_overrides_endpoint(self):
        settings = {"personality_engine": {"endpoint": "http://settings-endpoint"}}
        with patch.dict(os.environ, {"LLM_ENDPOINT": "http://env-endpoint"}):
            engine = PersonalityEngine(settings)
        assert engine._endpoint == "http://env-endpoint"

    def test_settings_api_key_used_when_no_env_var(self):
        settings = {"personality_engine": {"api_key": "settings-key"}}
        env = {k: v for k, v in os.environ.items() if k != "LLM_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            engine = PersonalityEngine(settings)
        assert engine._api_key == "settings-key"


class TestBuildModelString:
    def test_openai_no_prefix(self):
        engine = PersonalityEngine(
            {"personality_engine": {"provider": "openai", "model": "gpt-4o-mini"}}
        )
        assert engine._build_model_string() == "gpt-4o-mini"

    def test_anthropic_prefix(self):
        engine = PersonalityEngine(
            {"personality_engine": {"provider": "anthropic", "model": "claude-haiku-4-5-20251001"}}
        )
        assert engine._build_model_string() == "anthropic/claude-haiku-4-5-20251001"

    def test_ollama_prefix(self):
        engine = PersonalityEngine(
            {"personality_engine": {"provider": "ollama", "model": "llama3"}}
        )
        assert engine._build_model_string() == "ollama/llama3"

    def test_custom_no_prefix(self):
        engine = PersonalityEngine(
            {"personality_engine": {"provider": "custom", "model": "my-provider/my-model"}}
        )
        assert engine._build_model_string() == "my-provider/my-model"


class TestEnrich:
    def _make_settings(self, **kwargs):
        base = {
            "enabled": True,
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": "test-key",
            "endpoint": "",
        }
        base.update(kwargs)
        return {"personality_engine": base}

    def _make_mock_response(self, content: str):
        M = type("M", (), {"content": content})
        C = type("C", (), {"message": M()})
        R = type("R", (), {"choices": [C()]})
        return R()

    @pytest.mark.asyncio
    async def test_returns_original_when_disabled(self):
        engine = PersonalityEngine({"personality_engine": {"enabled": False}})
        result = await engine.enrich("hello")
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_returns_original_when_openclaw_connected(self):
        engine = PersonalityEngine(self._make_settings())
        engine.set_openclaw_connected(True)
        result = await engine.enrich("hello")
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_calls_litellm_acompletion_with_correct_params(self):
        engine = PersonalityEngine(
            self._make_settings(provider="openai", model="gpt-4o-mini", api_key="my-key")
        )
        mock_response = self._make_mock_response("Haro says hi!")

        with patch(
            "src.services.personality_engine.litellm.acompletion", new_callable=AsyncMock
        ) as mock_acompletion:
            mock_acompletion.return_value = mock_response
            result = await engine.enrich("hello world")

        assert result == "Haro says hi!"
        mock_acompletion.assert_called_once()
        call_kwargs = mock_acompletion.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["api_key"] == "my-key"
        assert call_kwargs["max_tokens"] == 150
        assert call_kwargs["timeout"] == 8

    @pytest.mark.asyncio
    async def test_returns_original_text_on_exception(self):
        engine = PersonalityEngine(self._make_settings())

        with patch(
            "src.services.personality_engine.litellm.acompletion", new_callable=AsyncMock
        ) as mock_acompletion:
            mock_acompletion.side_effect = Exception("LLM error")
            result = await engine.enrich("hello world")

        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_ollama_passes_api_base_not_api_key(self):
        engine = PersonalityEngine(
            self._make_settings(
                provider="ollama", model="llama3", endpoint="http://localhost:11434", api_key=""
            )
        )
        mock_response = self._make_mock_response("Haro beeps!")

        with patch(
            "src.services.personality_engine.litellm.acompletion", new_callable=AsyncMock
        ) as mock_acompletion:
            mock_acompletion.return_value = mock_response
            await engine.enrich("hello")

        call_kwargs = mock_acompletion.call_args.kwargs
        assert "api_key" not in call_kwargs
        assert call_kwargs.get("api_base") == "http://localhost:11434"


class TestUpdateSettings:
    def test_update_settings_changes_provider_model_api_key(self):
        engine = PersonalityEngine(
            {
                "personality_engine": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "api_key": "old-key",
                }
            }
        )
        engine.update_settings(
            {
                "personality_engine": {
                    "provider": "anthropic",
                    "model": "claude-haiku-4-5-20251001",
                    "api_key": "new-key",
                }
            }
        )
        assert engine._provider == "anthropic"
        assert engine._model == "claude-haiku-4-5-20251001"
        assert engine._api_key == "new-key"

    def test_update_settings_respects_env_override(self):
        engine = PersonalityEngine({"personality_engine": {"api_key": "old-key"}})
        with patch.dict(os.environ, {"LLM_API_KEY": "env-key"}):
            engine.update_settings({"personality_engine": {"api_key": "new-settings-key"}})
        assert engine._api_key == "env-key"
