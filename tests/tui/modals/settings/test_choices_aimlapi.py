"""AIMLAPI entries in the settings provider/model picker (choices.py)."""

from openhands_cli.aimlapi.models import AIMLAPI_MODELS, AIMLAPI_PROVIDER_LABEL
from openhands_cli.tui.modals.settings.choices import (
    get_model_options,
    get_provider_options,
)


def test_provider_picker_shows_aimlapi_label():
    options = get_provider_options()
    # The provider is presented under the AIMLAPI brand, routing value stays "aiml".
    assert (AIMLAPI_PROVIDER_LABEL, "aiml") in options
    # The bare lowercase "aiml" label is never shown to the user.
    assert ("aiml", "aiml") not in options


def test_model_options_for_aiml_are_the_curated_list():
    options = get_model_options("aiml")
    assert options == [(model, model) for model in AIMLAPI_MODELS]
    # A couple of the flagship ids are present.
    assert ("anthropic/claude-opus-5", "anthropic/claude-opus-5") in options
    assert ("x-ai/grok-4-5", "x-ai/grok-4-5") in options


def test_other_provider_does_not_get_aiml_models():
    openai_models = {value for _label, value in get_model_options("openai")}
    assert "anthropic/claude-opus-5" not in openai_models
