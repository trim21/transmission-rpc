# ruff: noqa: SLF001
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
    client._Client__http_client.request.side_effect = urllib3.exceptions.ConnectionError("fail")  # type: ignore[attr-defined]
    with pytest.raises(TransmissionConnectError):
        client._http_query({})


def test_http_query_timeout_error(client: Client) -> None:
    client._Client__http_client.request.side_effect = urllib3.exceptions.TimeoutError("fail")  # type: ignore[attr-defined]
    with pytest.raises(TransmissionTimeoutError):
        client._http_query({})


def test_http_query_auth_error(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(status=401, headers={}, data=b"")  # type: ignore[attr-defined]
    with pytest.raises(TransmissionAuthError):
        client._http_query({})


def test_http_query_too_many_requests(client: Client) -> None:
    conflict_resp = mock.Mock(status=409, headers={"x-transmission-session-id": "new_id"}, data=b"")
    client._Client__http_client.request.side_effect = [conflict_resp, conflict_resp, conflict_resp, conflict_resp]  # type: ignore[attr-defined]
    with pytest.raises(TransmissionError, match="too much request"):
        client._http_query({})


def test_request_invalid_json(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(status=200, headers={}, data=b"invalid json")  # type: ignore[attr-defined]
    with pytest.raises(TransmissionError, match="failed to parse response"):
        client._request(RpcMethod.TorrentGet)


def test_request_failure_result(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined]
        status=200, headers={}, data=json.dumps({"result": "failure", "arguments": {}}).encode()
    )
    with pytest.raises(TransmissionError, match='Query failed with result "failure"'):
        client._request(RpcMethod.TorrentGet)


def test_json_decode_error() -> None:
    """Cover JSON decode error handling in _request"""
    # Patch get_session so init doesn't make network calls
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        # Mock _http_query to return non-json string
        # We need to mock the instance method on the created instance 'c'
        c._http_query = mock.Mock(return_value="not json")  # type: ignore[method-assign]
        # We need a logger mock
        c.logger = mock.Mock()

        # Now call _request
        with pytest.raises(TransmissionError) as excinfo:
            c._request("method")  # type: ignore[arg-type]
        assert "failed to parse response as json" in str(excinfo.value)
        c.logger.exception.assert_called()


def test_request_errors() -> None:
    """Cover _request type checking and logic"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c.logger = mock.Mock()

        # Method check
        with pytest.raises(TypeError, match="request takes method as string"):
            c._request(method=123)  # type: ignore

        # Arguments check
        with pytest.raises(TypeError, match="request takes arguments should be dict"):
            c._request(method="m", arguments="not dict")  # type: ignore

        # Require ids
        with pytest.raises(ValueError, match="request require ids"):
            c._request(method="m", require_ids=True)  # type: ignore[arg-type]


def test_request_response_logic() -> None:
    """Cover response parsing logic"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c.logger = mock.Mock()
        # Enable debug to cover logging
        c.logger.isEnabledFor.return_value = True

        # Mock _http_query
        # 1. Missing result
        c._http_query = mock.Mock(return_value=json.dumps({"arguments": {}}))  # type: ignore[method-assign]
        with pytest.raises(TransmissionError, match="missing without result"):
            c._request("method")  # type: ignore[arg-type]

        c.logger.debug.assert_called()
