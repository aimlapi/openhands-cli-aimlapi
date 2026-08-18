"""Settings-screen wiring for AIMLAPI: the "Get API key" controls are shown
only when the AIMLAPI provider is selected, and the OAuth flow fills the key.
"""

from unittest.mock import AsyncMock, patch

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static

from openhands.sdk import Agent
from openhands_cli.tui.modals.settings import settings_screen as ss
from openhands_cli.tui.modals.settings.settings_screen import SettingsScreen


class _InMemoryStore:
    def __init__(self) -> None:
        self._agent: Agent | None = None

    def save(self, agent: Agent) -> None:
        self._agent = agent

    def load_from_disk(self) -> Agent | None:
        return self._agent

    def load_or_create(self, *args, **kwargs) -> Agent | None:
        return self._agent

    def create_from_env_overrides(self) -> Agent:
        raise NotImplementedError


class _SettingsApp(App):
    def __init__(self) -> None:
        super().__init__()
        self.settings_screen = SettingsScreen()

    def compose(self) -> ComposeResult:
        yield Static()

    def on_mount(self) -> None:
        self.push_screen(self.settings_screen)


@pytest.fixture
def _store(monkeypatch) -> _InMemoryStore:
    store = _InMemoryStore()
    monkeypatch.setattr(ss, "AgentStore", lambda: store)
    return store


@pytest.fixture
async def app(_store: _InMemoryStore):
    application = _SettingsApp()
    async with application.run_test() as pilot:
        yield application, pilot


async def test_aimlapi_is_default_provider_on_first_run(app):
    # No saved agent (first-time setup) -> AIMLAPI is preselected, so its
    # "Get API key" controls are visible without the user picking a provider.
    application, pilot = app
    screen = application.settings_screen
    await pilot.pause()
    assert str(screen.provider_select.value) == "aiml"
    assert screen.aimlapi_get_key_group.display is True


async def test_aimlapi_controls_shown_for_aiml_provider(app):
    application, pilot = app
    screen = application.settings_screen
    screen.mode_select.value = "basic"
    screen.provider_select.value = "aiml"
    screen._update_aimlapi_visibility()
    await pilot.pause()
    assert screen.aimlapi_get_key_group.display is True
    assert screen.query_one("#aimlapi_or").display is True
    assert screen.query_one("#api_key_hint", Static).display is True


async def test_aimlapi_controls_hidden_for_other_provider(app):
    application, pilot = app
    screen = application.settings_screen
    screen.mode_select.value = "basic"
    screen.provider_select.value = "openai"
    screen._update_aimlapi_visibility()
    await pilot.pause()
    assert screen.aimlapi_get_key_group.display is False


async def test_get_api_key_fills_field_and_shows_green_confirmation(app):
    application, pilot = app
    screen = application.settings_screen
    screen.mode_select.value = "basic"
    screen.provider_select.value = "aiml"
    screen._update_aimlapi_visibility()
    await pilot.pause()

    with patch.object(ss, "authorize", new=AsyncMock(return_value="sk-aiml-issued")):
        await screen._aimlapi_authorization_worker(
            screen.query_one("#aimlapi_get_key_button")
        )

    assert screen.api_key_input.value == "sk-aiml-issued"
    assert screen.query_one("#aimlapi_key_generated", Static).display is True
