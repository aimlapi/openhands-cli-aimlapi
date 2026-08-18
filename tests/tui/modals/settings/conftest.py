"""Shared fixtures for the settings-modal tests.

The settings screen warms the AIMLAPI model catalog from ``GET /v1/models`` in a
background worker on mount. Stub that network call out for every test in this
package so the suite stays hermetic and fast; tests that care about the catalog
patch the model helpers directly.
"""

from unittest.mock import AsyncMock

import pytest

from openhands_cli.tui.modals.settings import settings_screen as _settings_screen


@pytest.fixture(autouse=True)
def _stub_aimlapi_model_refresh(monkeypatch):
    monkeypatch.setattr(
        _settings_screen,
        "refresh_model_cache",
        AsyncMock(return_value=None),
    )
