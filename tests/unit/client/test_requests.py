import json
import logging
import pathlib
from typing import Any
from unittest import mock

import pytest
import urllib3

from transmission_rpc.client import Client
from transmission_rpc.error import (
    TransmissionAuthError,
    TransmissionConnectError,
    TransmissionError,
    TransmissionTimeoutError,
)


def test_http_query_connection_error() -> None:
    """Verify that connection errors from urllib3 are raised as TransmissionConnectError."""
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        mock_req.side_effect = urllib3.exceptions.ConnectionError("fail")
        # Client initialization calls get_session, which triggers the query
        with pytest.raises(TransmissionConnectError):
            Client()


def test_http_query_timeout_error() -> None:
    """Verify that timeout errors from urllib3 are raised as TransmissionTimeoutError."""
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        mock_req.side_effect = urllib3.exceptions.TimeoutError("fail")
        with pytest.raises(TransmissionTimeoutError):
            Client()


def test_http_query_auth_error() -> None:
    """Verify that 401/403 responses are raised as TransmissionAuthError."""
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        mock_req.return_value = mock.Mock(status=401, headers={}, data=b"")
        with pytest.raises(TransmissionAuthError):
            Client()


def test_http_query_too_many_requests() -> None:
    """Verify that the client enforces a retry limit on 409 Conflict responses."""
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        # Client should retry a few times then raise or succeed.
        # If it keeps getting 409, it should eventually fail.
        conflict_resp = mock.Mock(status=409, headers={"x-transmission-session-id": "new_id"}, data=b"")
        mock_req.side_effect = [conflict_resp] * 10

        with pytest.raises(TransmissionError, match="too much request"):
            Client()


def test_request_invalid_json(success_response: Any) -> None:
    """Verify that invalid JSON in the response raises a TransmissionError and logs the exception."""
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        # 1. Init success (must include version info)
        mock_req.side_effect = [
            success_response(),
            # 2. Invalid JSON for get_torrents
            mock.Mock(status=200, headers={}, data=b"invalid json"),
        ]

        # Inject logger via constructor, using spec to pass isinstance check
        c = Client(logger=mock.Mock(spec=logging.Logger))

        with pytest.raises(TransmissionError, match="failed to parse response"):
            c.get_torrents()

        c.logger.exception.assert_called()


def test_request_failure_result(success_response: Any) -> None:
    """Verify that a JSON response with 'result': 'failure' raises a TransmissionError."""
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        # 1. Init success
        mock_req.side_effect = [
            success_response(),
            # 2. Failure response
            mock.Mock(status=200, headers={}, data=json.dumps({"result": "failure", "arguments": {}}).encode()),
        ]

        c = Client()
        with pytest.raises(TransmissionError, match='Query failed with result "failure"'):
            c.get_torrents()


def test_request_missing_result(success_response: Any) -> None:
    """Verify that a response missing the 'result' field raises a TransmissionError."""
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        mock_req.side_effect = [
            success_response(),
            mock.Mock(status=200, headers={}, data=json.dumps({"arguments": {}}).encode()),
        ]

        # Inject logger via constructor, using spec to pass isinstance check
        c = Client(logger=mock.Mock(spec=logging.Logger))

        with pytest.raises(TransmissionError, match="missing without result"):
            c.get_torrents()

        c.logger.debug.assert_called()


def test_void_methods_return_none_on_success(mock_network: Any, success_response: Any, tmp_path: pathlib.Path) -> None:
    """
    Verify that simple pass-through methods (void return) execute without error and return None
    upon a successful RPC response.
    """
    mock_network.return_value = success_response()
    c = Client()

    c.remove_torrent(ids=1)
    c.start_torrent(ids=1)
    c.stop_torrent(ids=1)
    c.verify_torrent(ids=1)
    c.reannounce_torrent(ids=1)
    c.move_torrent_data(ids=1, location=str(tmp_path))
    c.queue_top(ids=1)
    c.queue_bottom(ids=1)
    c.queue_up(ids=1)
    c.queue_down(ids=1)
    c.set_session(alt_speed_enabled=True)
    c.session_close()

    # rename_torrent_path returns tuple
    mock_network.return_value = success_response({"path": "/a", "name": "b"})
    assert c.rename_torrent_path(1, "/path", "name") == ("/a", "b")

    # port_test returns object
    mock_network.return_value = success_response({"port-is-open": True})
    assert c.port_test().port_is_open is True


def test_blocklist_update(mock_network: Any, success_response: Any) -> None:
    """Verify that blocklist_update calls the correct RPC method and returns the blocklist size integer."""
    mock_network.side_effect = [success_response(), success_response({"blocklist-size": 123})]
    c = Client()
    assert c.blocklist_update() == 123


def test_get_recently_active_torrents(mock_network: Any, success_response: Any) -> None:
    """Verify get_recently_active_torrents structure."""
    mock_network.side_effect = [success_response(), success_response({"torrents": [], "removed": [1, 2]})]
    c = Client()
    _, removed = c.get_recently_active_torrents()
    assert removed == [1, 2]


def test_get_recently_active_with_arguments(mock_network: Any, success_response: Any) -> None:
    """
    Verify argument set logic in get_recently_active_torrents.
    """
    mock_network.side_effect = [success_response(), success_response({"torrents": [], "removed": []})]
    c = Client()
    # Passing arguments triggers the 'if arguments:' block
    c.get_recently_active_torrents(arguments=["name"])

    sent_args = mock_network.call_args[1]["json"]["arguments"]["fields"]
    assert "name" in sent_args
    assert "hashString" in sent_args
