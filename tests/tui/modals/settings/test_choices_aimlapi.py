"""AIMLAPI entries in the settings provider/model picker (choices.py)."""

from rich.text import Text

from openhands_cli.aimlapi import models as aimlapi_models
from openhands_cli.aimlapi.models import AIMLAPI_PROVIDER_LABEL
from openhands_cli.tui.modals.settings import choices as choices_module
from openhands_cli.tui.modals.settings.choices import (
    get_model_options,
    get_provider_options,
)


def _label_text(label) -> str:
    """Plain string of a dropdown label (labels may be styled rich Text)."""
    return getattr(label, "plain", label)


def test_provider_picker_shows_aimlapi_label():
    options = get_provider_options()
    aiml = [(label, value) for label, value in options if value == "aiml"]
    # The provider is presented under the AIMLAPI brand, routing value stays "aiml".
    assert len(aiml) == 1
    assert _label_text(aiml[0][0]) == f"{AIMLAPI_PROVIDER_LABEL} (Recommended)"
    # The bare lowercase "aiml" label is never shown to the user.
    assert ("aiml", "aiml") not in options


def test_aimlapi_is_first_in_provider_list():
    options = get_provider_options()
    label, value = options[0]
    assert value == "aiml"
    assert _label_text(label) == f"{AIMLAPI_PROVIDER_LABEL} (Recommended)"


def test_recommended_suffix_is_dimmed():
    options = get_provider_options()
    label = next(label for label, value in options if value == "aiml")
    assert isinstance(label, Text)
    # "aimlapi.com" is normal; only " (Recommended)" carries the dim style.
    spans = {(label.plain[s.start : s.end], str(s.style)) for s in label.spans}
    assert (" (Recommended)", "dim") in spans


def test_model_options_for_aiml_come_from_available_models(monkeypatch):
    # get_model_options("aiml") maps whatever the (cache-backed) catalog returns.
    catalog = ["anthropic/claude-opus-5", "openai/gpt-4o", "x-ai/grok-4-5"]
    monkeypatch.setattr(choices_module, "available_models", lambda: catalog)
    options = get_model_options("aiml")
    assert options == [(m, m) for m in catalog]


def test_available_models_falls_back_when_no_cache(monkeypatch):
    # With no usable cache, the built-in flagship fallback is served.
    monkeypatch.setattr(aimlapi_models, "_read_cache", lambda: None)
    assert aimlapi_models.available_models() == list(aimlapi_models.AIMLAPI_MODELS)


def test_parse_chat_ids_filters_and_dedupes():
    payload = {
        "data": [
            {"id": "openai/gpt-4o", "type": "openai/chat-completions"},
            # Same id, non-chat endpoint -> ignored (dedupe across endpoints).
            {"id": "openai/gpt-4o", "type": "openai/responses/submit"},
            {"id": "openai/dall-e-3", "type": "openai/image-generations"},
            {"id": "x-ai/grok-4-5", "type": "openai/chat-completions"},
        ]
    }
    assert aimlapi_models._parse_chat_ids(payload) == [
        "openai/gpt-4o",
        "x-ai/grok-4-5",
    ]


def test_other_provider_does_not_get_aiml_models():
    openai_models = {value for _label, value in get_model_options("openai")}
    assert "anthropic/claude-opus-5" not in openai_models
