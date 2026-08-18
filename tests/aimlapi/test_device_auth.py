"""Unit tests for the AIMLAPI "Get API key" device-authorization client."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from openhands_cli.aimlapi import device_auth
from openhands_cli.aimlapi.device_auth import (
    AimlapiAuthError,
    AuthorizationPollResult,
    AuthorizationRequest,
    _verification_uri,
    authorize,
    poll_authorization,
    start_authorization,
)


_CLIENT = "openhands_cli.aimlapi.device_auth.httpx.AsyncClient"


def _mock_async_client(response: httpx.Response) -> MagicMock:
    """Stand in for ``httpx.AsyncClient(...)`` used as an async context manager."""
    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    client.post = AsyncMock(return_value=response)
    return client


def _auth_request(expires_in: float = 900.0) -> AuthorizationRequest:
    return AuthorizationRequest(
        request_id="aar_1",
        device_code="aad_1",
        verification_uri="https://front.example.com/app/agent/authorize?request=aar_1",
        interval=1,
        expires_at=time.time() + expires_in,
    )


@pytest.fixture(autouse=True)
def _pin_env(monkeypatch):
    """Deterministic endpoints/partner regardless of the ambient environment."""
    monkeypatch.setenv("AIMLAPI_APP_URL", "https://app.example.com")
    monkeypatch.setenv("AIMLAPI_VERIFICATION_BASE_URL", "https://front.example.com/app")
    monkeypatch.setenv("AIMLAPI_PARTNER_ID", "part_test")
    monkeypatch.delenv("AIMLAPI_PARTNER_NAME", raising=False)
    monkeypatch.delenv("AIMLAPI_REQUESTED_USD_LIMIT_MINOR", raising=False)


def test_verification_uri_uses_app_path():
    assert (
        _verification_uri("aar_123")
        == "https://front.example.com/app/agent/authorize?request=aar_123"
    )


async def test_start_authorization_success():
    resp = httpx.Response(
        201,
        json={
            "requestId": "aar_1",
            "deviceCode": "aad_1",
            "interval": 7,
            "expiresIn": 600,
        },
    )
    with patch(_CLIENT, return_value=_mock_async_client(resp)):
        auth = await start_authorization()
    assert auth.request_id == "aar_1"
    assert auth.device_code == "aad_1"
    assert auth.interval == 7
    assert auth.verification_uri.endswith("/app/agent/authorize?request=aar_1")


async def test_start_authorization_surfaces_error_body():
    resp = httpx.Response(403, json={"message": "Unknown or disabled partner"})
    with patch(_CLIENT, return_value=_mock_async_client(resp)):
        with pytest.raises(AimlapiAuthError, match="Unknown or disabled partner"):
            await start_authorization()


async def test_poll_pending():
    resp = httpx.Response(200, json={"status": "pending"})
    with patch(_CLIENT, return_value=_mock_async_client(resp)):
        result = await poll_authorization(_auth_request())
    assert result.status == "pending"
    assert result.api_key == ""


async def test_poll_ready_returns_key():
    resp = httpx.Response(200, json={"status": "completed", "apiKey": "sk-aiml-xyz"})
    with patch(_CLIENT, return_value=_mock_async_client(resp)):
        result = await poll_authorization(_auth_request())
    assert result.status == "ready"
    assert result.api_key == "sk-aiml-xyz"


async def test_poll_accepts_alternate_key_fields():
    resp = httpx.Response(200, json={"access_token": "sk-alt"})
    with patch(_CLIENT, return_value=_mock_async_client(resp)):
        result = await poll_authorization(_auth_request())
    assert result.status == "ready"
    assert result.api_key == "sk-alt"


async def test_poll_terminal_status():
    resp = httpx.Response(200, json={"status": "denied"})
    with patch(_CLIENT, return_value=_mock_async_client(resp)):
        result = await poll_authorization(_auth_request())
    assert result.status == "denied"


async def test_poll_expired_short_circuits():
    # Past expiry: returns "expired" without making an HTTP call.
    result = await poll_authorization(_auth_request(expires_in=-1))
    assert result.status == "expired"


async def test_authorize_opens_browser_and_returns_key():
    auth = _auth_request()
    opened: list[str] = []
    with (
        patch.object(device_auth, "start_authorization", AsyncMock(return_value=auth)),
        patch.object(
            device_auth,
            "poll_authorization",
            AsyncMock(
                return_value=AuthorizationPollResult(status="ready", api_key="k")
            ),
        ),
    ):
        key = await authorize(open_browser=opened.append)
    assert key == "k"
    assert opened == [auth.verification_uri]


async def test_authorize_raises_on_terminal_status():
    auth = _auth_request()
    with (
        patch.object(device_auth, "start_authorization", AsyncMock(return_value=auth)),
        patch.object(
            device_auth,
            "poll_authorization",
            AsyncMock(return_value=AuthorizationPollResult(status="denied")),
        ),
    ):
        with pytest.raises(AimlapiAuthError, match="denied"):
            await authorize(open_browser=lambda _url: None)


async def test_authorize_tolerates_transient_poll_errors():
    # A long sign-up/payment detour can hit momentary network/server blips; the
    # flow must keep polling and still succeed once the key is issued.
    auth = _auth_request()
    poll = AsyncMock(
        side_effect=[
            AimlapiAuthError("temporary network blip"),
            AuthorizationPollResult(status="pending"),
            AimlapiAuthError("temporary 502"),
            AuthorizationPollResult(status="ready", api_key="k"),
        ]
    )
    with (
        patch.object(device_auth, "start_authorization", AsyncMock(return_value=auth)),
        patch.object(device_auth, "poll_authorization", poll),
        patch.object(device_auth.asyncio, "sleep", AsyncMock()),
    ):
        key = await authorize(open_browser=lambda _url: None)
    assert key == "k"


async def test_authorize_gives_up_after_repeated_errors():
    auth = _auth_request()
    poll = AsyncMock(side_effect=AimlapiAuthError("still broken"))
    with (
        patch.object(device_auth, "start_authorization", AsyncMock(return_value=auth)),
        patch.object(device_auth, "poll_authorization", poll),
        patch.object(device_auth.asyncio, "sleep", AsyncMock()),
    ):
        with pytest.raises(AimlapiAuthError, match="still broken"):
            await authorize(open_browser=lambda _url: None)
    assert poll.await_count == device_auth.MAX_CONSECUTIVE_POLL_ERRORS


async def test_authorize_raises_on_expired_status():
    auth = _auth_request()
    with (
        patch.object(device_auth, "start_authorization", AsyncMock(return_value=auth)),
        patch.object(
            device_auth,
            "poll_authorization",
            AsyncMock(return_value=AuthorizationPollResult(status="expired")),
        ),
        patch.object(device_auth.asyncio, "sleep", AsyncMock()),
    ):
        with pytest.raises(AimlapiAuthError, match="expired"):
            await authorize(open_browser=lambda _url: None)
