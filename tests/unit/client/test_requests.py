import json
from unittest import mock

import pytest
import urllib3

from transmission_rpc.client import Client
from transmission_rpc.constants import RpcMethod
from transmission_rpc.error import (
    TransmissionAuthError,
    TransmissionConnectError,
    TransmissionError,
    TransmissionTimeoutError,
)


def test_http_query_connection_error(client: Client) -> None:
    """Verify that connection errors from urllib3 are raised as TransmissionConnectError."""
    client._Client__http_client.request.side_effect = urllib3.exceptions.ConnectionError("fail")  # type: ignore[attr-defined]  # noqa: SLF001
    with pytest.raises(TransmissionConnectError):
        client._http_query({})  # noqa: SLF001


def test_http_query_timeout_error(client: Client) -> None:
    """Verify that timeout errors from urllib3 are raised as TransmissionTimeoutError."""
    client._Client__http_client.request.side_effect = urllib3.exceptions.TimeoutError("fail")  # type: ignore[attr-defined]  # noqa: SLF001
    with pytest.raises(TransmissionTimeoutError):
        client._http_query({})  # noqa: SLF001


def test_http_query_auth_error(client: Client) -> None:
    """Verify that 401/403 responses are raised as TransmissionAuthError."""
    client._Client__http_client.request.return_value = mock.Mock(status=401, headers={}, data=b"")  # type: ignore[attr-defined]  # noqa: SLF001
    with pytest.raises(TransmissionAuthError):
        client._http_query({})  # noqa: SLF001


def test_http_query_too_many_requests(client: Client) -> None:
    """Verify that the client enforces a retry limit on 409 Conflict responses."""
    conflict_resp = mock.Mock(status=409, headers={"x-transmission-session-id": "new_id"}, data=b"")
    client._Client__http_client.request.side_effect = [conflict_resp, conflict_resp, conflict_resp, conflict_resp]  # type: ignore[attr-defined]  # noqa: SLF001
    with pytest.raises(TransmissionError, match="too much request"):
        client._http_query({})  # noqa: SLF001


def test_request_invalid_json(client: Client) -> None:
    """Verify that invalid JSON in the response raises a TransmissionError and logs the exception."""
    client.logger = mock.Mock()
    client._Client__http_client.request.return_value = mock.Mock(status=200, headers={}, data=b"invalid json")  # type: ignore[attr-defined]  # noqa: SLF001
    with pytest.raises(TransmissionError, match="failed to parse response"):
        client._request(RpcMethod.TorrentGet)  # noqa: SLF001
    client.logger.exception.assert_called()


def test_request_failure_result(client: Client) -> None:
    """Verify that a JSON response with 'result': 'failure' raises a TransmissionError."""
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined]  # noqa: SLF001
        status=200, headers={}, data=json.dumps({"result": "failure", "arguments": {}}).encode()
    )
    with pytest.raises(TransmissionError, match='Query failed with result "failure"'):
        client._request(RpcMethod.TorrentGet)  # noqa: SLF001


def test_request_errors() -> None:
    """Cover _request type checking and logic"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c.logger = mock.Mock()

        # Method check
        with pytest.raises(TypeError, match="request takes method as string"):
            c._request(method=123)  # type: ignore  # noqa: SLF001

        # Arguments check
        with pytest.raises(TypeError, match="request takes arguments should be dict"):
            c._request(method="m", arguments="not dict")  # type: ignore  # noqa: SLF001

        # Require ids
        with pytest.raises(ValueError, match="request require ids"):
            c._request(method="m", require_ids=True)  # type: ignore[arg-type]  # noqa: SLF001


def test_request_response_logic() -> None:
    """Cover response parsing logic"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c.logger = mock.Mock()
        # Enable debug to cover logging
        c.logger.isEnabledFor.return_value = True

        # Mock _http_query
        # 1. Missing result
        c._http_query = mock.Mock(return_value=json.dumps({"arguments": {}}))  # type: ignore[method-assign]  # noqa: SLF001
        with pytest.raises(TransmissionError, match="missing without result"):
            c._request("method")  # type: ignore[arg-type]  # noqa: SLF001

        c.logger.debug.assert_called()
