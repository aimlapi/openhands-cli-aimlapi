"""Tests for openhands_cli.tui.modals.settings.choices."""

from openhands_cli.tui.modals.settings.choices import get_provider_options


def test_aimlapi_provider_is_listed_first() -> None:
    """The AIMLAPI provider is pinned to the top of the dropdown."""
    options = get_provider_options()
    assert options, "expected at least one provider option"
    label, value = options[0]
    assert value == "aiml"
    # Label may be a styled rich Text; compare its plain string.
    assert getattr(label, "plain", label) == "aimlapi.com (Recommended)"


def test_openhands_provider_is_listed_second() -> None:
    """'openhands' follows AIMLAPI at the top of the list.

    Regression test for #712: the dropdown was rendering providers strictly
    alphabetically, which pushed 'openhands' below entries like 'anthropic'.
    """
    options = get_provider_options()
    values = [value for _label, value in options]
    assert values[1] == "openhands"


def test_remaining_providers_are_sorted_alphabetically() -> None:
    """Providers other than the two pinned ones stay alphabetically sorted."""
    options = get_provider_options()
    values = [value for _label, value in options]
    other_values = [v for v in values if v not in ("aiml", "openhands")]
    assert other_values == sorted(other_values)
