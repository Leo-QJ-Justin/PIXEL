# LiteLLM Personality Engine Integration

## Summary

Replace the hand-rolled multi-provider HTTP client with LiteLLM as a unified API router, update the settings UI to support a curated dropdown of providers, and wire the personality engine into the app so speech bubble text is actually enriched via LLM.

## Context

The personality engine (`src/services/personality_engine.py`, `src/services/llm_client.py`) exists but is dead code — never instantiated or called. The current `LLMClient` has 3 separate aiohttp methods with provider-specific response parsing for OpenAI, OpenRouter, and Ollama. The settings UI has radio buttons for these 3 providers.

## Design

### 1. LiteLLM Backend

**Replace `src/services/llm_client.py`** with a single async function wrapping `litellm.acompletion()`.

LiteLLM routes via model string prefix:
- `gpt-4o-mini` → OpenAI
- `openrouter/meta-llama/llama-3-8b-instruct` → OpenRouter
- `ollama/llama3` → Ollama
- `anthropic/claude-haiku-4-5-20251001` → Anthropic
- Any other litellm-supported provider

**Settings structure** (replaces per-provider keys):
```json
"personality_engine": {
    "enabled": false,
    "provider": "openai",
    "model": "gpt-4o-mini",
    "api_key": "",
    "endpoint": ""
}
```

### 2. Settings UI

**Provider dropdown** — curated list + Custom:
- OpenAI, Anthropic, OpenRouter, Groq, Mistral, Google Gemini, Together AI, Deepseek, Ollama, Custom

**Dynamic fields per provider:**
- **Cloud providers** (OpenAI, Anthropic, etc.) → API Key (password field) + Model name
- **Ollama** → Endpoint URL (default `http://localhost:11434`) + Model name, no API key
- **Custom** → API key + Endpoint URL + raw litellm model string

**Default model per provider** — auto-fills a sensible default when provider changes (e.g. `gpt-4o-mini` for OpenAI, `llama3` for Ollama). User can override.

**API key persistence:**
- Saved in `settings.json` (gitignored) via the existing settings save mechanism
- `.env` variables override `settings.json` values if present
- Both files are in `.gitignore` — keys are never committed

### 3. Wiring the Personality Engine

**Flow:** Speech bubble text → `PersonalityEngine.enrich()` → LiteLLM → styled text displayed

**Connection points:**
- `main.py` instantiates `PersonalityEngine`, passes it to `PetWidget`
- Before `SpeechBubble.show_message(text)`, text goes through `await engine.enrich(text)`
- Speech bubble shows original text immediately, updates once LLM responds (no user-visible delay)
- If enrichment fails (bad key, timeout, provider down), original text displays as-is — silent fallback
- OpenClaw bypass preserved: `set_openclaw_connected(True)` skips enrichment

### 4. Provider-to-LiteLLM Mapping

The UI provider dropdown maps to litellm model prefixes:

| UI Provider    | LiteLLM model format                   | Needs API Key | Needs Endpoint |
|----------------|----------------------------------------|---------------|----------------|
| OpenAI         | `{model}`                              | Yes           | No             |
| Anthropic      | `anthropic/{model}`                    | Yes           | No             |
| OpenRouter     | `openrouter/{model}`                   | Yes           | No             |
| Groq           | `groq/{model}`                         | Yes           | No             |
| Mistral        | `mistral/{model}`                      | Yes           | No             |
| Google Gemini  | `gemini/{model}`                       | Yes           | No             |
| Together AI    | `together_ai/{model}`                  | Yes           | No             |
| Deepseek       | `deepseek/{model}`                     | Yes           | No             |
| Ollama         | `ollama/{model}`                       | No            | Yes            |
| Custom         | raw litellm string                     | Optional      | Optional       |

API key is passed to litellm via the appropriate environment variable or `api_key` parameter at call time.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `pyproject.toml` | MODIFY | Add `litellm` dependency |
| `src/services/llm_client.py` | DELETE | Replaced by litellm |
| `src/services/personality_engine.py` | MODIFY | Single `litellm.acompletion()` call, no manual fallback chain |
| `src/ui/settings/tab_personality.py` | MODIFY | Dropdown + dynamic fields, replace radio buttons |
| `config.py` | MODIFY | New default settings shape |
| `settings.json` | MODIFY | Updated defaults |
| `main.py` | MODIFY | Instantiate PersonalityEngine, pass to PetWidget |
| `src/ui/pet_window.py` | MODIFY | Call `enrich()` before speech bubble display |
| `tests/ui/test_settings_tab_personality.py` | MODIFY | Update for new UI structure |
| `tests/services/test_personality_engine.py` | NEW | Unit tests for engine with mocked litellm |

## No Migration Needed

Old `settings.json` keys (`openai_api_key`, `openrouter_api_key`, etc.) are silently ignored. Users re-enter their key in the new UI. Acceptable since the engine was never functional.
