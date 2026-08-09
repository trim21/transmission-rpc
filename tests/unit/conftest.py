import json
from collections.abc import Generator
from typing import Any
from unittest import mock

import pytest

from transmission_rpc.client import Client


@pytest.fixture
def success_response() -> Any:
    """
    Helper to create a standard JSON-RPC 2.0 success response mock.
    Returns a callable that produces the response.
    """

    def _response(result: dict[str, Any] | None = None) -> mock.Mock:
        result = result or {}
        # Inject default version info required for Client init
        result.setdefault("rpc_version", 18)
        result.setdefault("version", "4.1.0")
        result.setdefault("rpc_version_semver", "6.0.0")

        return mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "0"},
            data=json.dumps({"jsonrpc": "2.0", "result": result, "id": 1}).encode(),
        )

    return _response


@pytest.fixture
def legacy_response() -> Any:
    """
    Helper to create a legacy (pre-4.1.0 bespoke) success response mock.
    """

    def _response(arguments: dict[str, Any] | None = None) -> mock.Mock:
        args = arguments or {}
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
                    "jsonrpc": "2.0",
                    "result": {"rpc_version": 18, "rpc_version_semver": "6.0.0", "version": "4.1.0"},
                    "id": 1,
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
