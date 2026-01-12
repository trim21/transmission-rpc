import json
from collections.abc import Generator
from typing import Any
from unittest import mock

import pytest

from transmission_rpc.client import Client


@pytest.fixture
def success_response() -> Any:
    """
    Helper to create a standard success response mock.
    Returns a callable that produces the response.
    """

    def _response(arguments: dict[str, Any] | None = None) -> mock.Mock:
        args = arguments or {}
        # Inject default version info required for Client init
        args.setdefault("rpc-version", 17)
        args.setdefault("version", "4.0.0")
        args.setdefault("rpc-version-semver", "5.0.0")

        return mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "0"},
            data=json.dumps({"result": "success", "arguments": args}).encode(),
        )

    return _response


@pytest.fixture
def mock_network() -> Generator[mock.MagicMock, None, None]:
    """
    Fixture to patch the urllib3.HTTPConnectionPool.request method.

    This allows tests to intercept network calls and assert on the arguments
    passed to the request without making actual network connections.
    """
    with mock.patch("urllib3.HTTPConnectionPool.request") as m:
        yield m


@pytest.fixture
def mock_http_client() -> Generator[mock.MagicMock, None, None]:
    """
    Mock the low-level urllib3 connection to simulate RPC responses without a real daemon.
    This fixture is used by the 'client' fixture below.
    """
    with mock.patch("transmission_rpc.client.urllib3.HTTPConnectionPool") as m:
        # Default response for the initial session setup call in Client.__init__
        m.return_value.request.return_value = mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "session_id"},
            data=json.dumps(
                {
                    "result": "success",
                    "arguments": {"rpc-version": 17, "rpc-version-semver": "5.3.0", "version": "4.0.0"},
                }
            ).encode("utf-8"),
        )
        yield m


@pytest.fixture
def client(mock_http_client: Any) -> Client:
    """
    Create a Client instance with the mocked HTTP client.
    Useful for unit tests that need a pre-initialized Client.
    """
    return Client()
