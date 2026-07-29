"""AIMLAPI provider metadata for the CLI settings picker.

AIMLAPI (https://aimlapi.com) exposes 300+ models behind one OpenAI-compatible
key. LiteLLM routes them via its ``aiml`` provider, so a model saved as
``aiml/<catalog-id>`` reaches AIMLAPI. The provider already appears in the
picker via litellm/the SDK as the bare id ``aiml``; this module (1) presents it
under the AIMLAPI brand (label ``aimlapi.com``) and (2) supplies the model list
for it.

The model list is fetched live from ``GET /v1/models`` (public, no key needed)
and filtered to chat-completions models, so the picker always reflects the full
current AIMLAPI chat catalog. ``AIMLAPI_MODELS`` below is the built-in fallback
used only when the catalog cannot be fetched (offline / first run before the
cache warms).
"""

import json
import os
import time
from pathlib import Path

import httpx
from rich.text import Text


# LiteLLM's registered provider id for AIMLAPI. This value MUST stay "aiml":
# litellm only knows the provider as "aiml" (there is no "aimlapi" alias), and
# the settings screen saves a basic-mode choice as ``{provider}/{model}`` — so a
# selection routes as ``aiml/<catalog-id>``. It is never shown to the user; the
# picker displays AIMLAPI_PROVIDER_LABEL instead.
AIML_LITELLM_PROVIDER = "aiml"
# How AIMLAPI is shown in the provider dropdown.
AIMLAPI_PROVIDER_LABEL = "aimlapi.com"
# Appended to the label to flag AIMLAPI as the suggested choice; rendered dimmer
# than the provider name so it reads as a hint, not part of the id.
AIMLAPI_RECOMMENDED_SUFFIX = " (Recommended)"


def aimlapi_provider_prompt() -> Text:
    """The provider-dropdown label: ``aimlapi.com`` + a muted ``(Recommended)``."""
    prompt = Text(AIMLAPI_PROVIDER_LABEL)
    prompt.append(AIMLAPI_RECOMMENDED_SUFFIX, style="dim")
    return prompt


# Built-in fallback list — flagship tool-calling chat ids, used only when the
# live catalog is unavailable. Catalog ids as returned by ``GET /v1/models``
# (the picker adds the ``aiml/`` provider prefix when saving).
AIMLAPI_MODELS: list[str] = [
    # Anthropic
    "anthropic/claude-opus-5",
    "anthropic/claude-opus-4.8",
    "anthropic/claude-sonnet-5",
    "anthropic/claude-fable-5",
    # OpenAI
    "openai/gpt-5.6-luna-pro",
    "openai/gpt-5.6-sol-pro",
    "openai/gpt-5.6-terra-pro",
    # Google
    "google/gemini-3.6-flash",
    # xAI
    "x-ai/grok-4-5",
    # DeepSeek
    "deepseek/deepseek-v4-pro",
    # Alibaba Qwen
    "alibaba/qwen3.7-max",
    # Zhipu GLM
    "zhipu/glm-5.2",
    # Moonshot
    "moonshot/kimi-k3",
    # MiniMax
    "minimax/minimax-m3",
]

# AIMLAPI ``GET /v1/models`` returns one entry per (model × endpoint type). Chat
# models carry a type ending in "chat-completions" — that is the set litellm's
# ``aiml`` provider can drive as a coding agent.
_CHAT_TYPE_SUFFIX = "chat-completions"
# The models list is public; keep the request short so a slow network never
# blocks the settings UI (the cache-warm runs in a background worker anyway).
_HTTP_TIMEOUT_SECONDS = 6.0
# On-disk cache so the picker is instant on subsequent opens; refreshed in the
# background when stale.
_CACHE_PATH = Path.home() / ".openhands" / "aimlapi_models_cache.json"
_CACHE_TTL_SECONDS = 24 * 60 * 60


def _models_url() -> str:
    """Base is litellm's ``AIML_API_BASE`` (so staging models come from staging).

    ``AIML_API_BASE`` already includes the ``/v1`` suffix (litellm default
    ``https://api.aimlapi.com/v1``); the models list lives at ``/models``.
    """
    base = (os.getenv("AIML_API_BASE") or "https://api.aimlapi.com/v1").strip()
    return f"{base.rstrip('/')}/models"


def _parse_chat_ids(payload: object) -> list[str]:
    """Extract sorted, de-duplicated chat-model ids from a /v1/models payload."""
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        return []
    seen: set[str] = set()
    ids: list[str] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        if not str(entry.get("type", "")).endswith(_CHAT_TYPE_SUFFIX):
            continue
        model_id = str(entry.get("id", "")).strip()
        if model_id and model_id not in seen:
            seen.add(model_id)
            ids.append(model_id)
    return sorted(ids)


def _read_cache() -> list[str] | None:
    """Return cached model ids (any age), or None if the cache is unusable."""
    try:
        raw = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    models = raw.get("models") if isinstance(raw, dict) else None
    if isinstance(models, list) and models:
        return [str(m) for m in models]
    return None


def _cache_is_fresh() -> bool:
    try:
        age = time.time() - _CACHE_PATH.stat().st_mtime
    except OSError:
        return False
    return age < _CACHE_TTL_SECONDS


def _write_cache(models: list[str]) -> None:
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_PATH.write_text(json.dumps({"models": models}), encoding="utf-8")
    except OSError:
        # A non-writable cache is non-fatal — the list still works this session.
        pass


def available_models() -> list[str]:
    """Model ids for the picker: cached live catalog, else built-in fallback.

    Never does network I/O — safe to call synchronously from the UI. The live
    catalog is warmed into the cache by ``refresh_model_cache`` in a worker.
    """
    return _read_cache() or list(AIMLAPI_MODELS)


async def fetch_models_from_api() -> list[str]:
    """Fetch and filter the live chat-model catalog. Raises on network error."""
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_SECONDS) as client:
        response = await client.get(
            _models_url(), headers={"Accept": "application/json"}
        )
    response.raise_for_status()
    return _parse_chat_ids(response.json())


async def refresh_model_cache(force: bool = False) -> list[str] | None:
    """Refresh the on-disk catalog cache if stale. Returns the ids, or None.

    Best-effort: any failure leaves the previous cache/fallback in place and
    returns None so callers can quietly keep the existing options.
    """
    if not force and _cache_is_fresh():
        return _read_cache()
    try:
        models = await fetch_models_from_api()
    except (httpx.HTTPError, ValueError):
        return None
    if models:
        _write_cache(models)
    return models or None
