import json
from typing import Any, cast
from unittest import mock

import pytest

from transmission_rpc.client import Client
from transmission_rpc.error import TransmissionError


def _jsonrpc2_response(data: dict[str, Any] | None = None, *, req_id: int = 1) -> mock.Mock:
    """Helper: build a JSON-RPC 2.0 success response mock."""
    return mock.Mock(
        status=200,
        headers={"x-transmission-session-id": "sess"},
        data=json.dumps({"jsonrpc": "2.0", "result": data or {}, "id": req_id}).encode(),
    )


def _jsonrpc2_init_response() -> mock.Mock:
    """Helper: build the session-get bootstrap response for a Transmission 4.1.0 server."""
    # The first request always uses the old protocol; the server still answers it.
    return mock.Mock(
        status=200,
        headers={"x-transmission-session-id": "sess"},
        data=json.dumps({
            "result": "success",
            "arguments": {"rpc-version": 18, "rpc-version-semver": "6.0.0", "version": "4.1.0"},
        }).encode(),
    )


def test_start_all_bypass_queue(mock_network: Any, success_response: Any) -> None:
    """
    Verify that `start_all(bypass_queue=True)` correctly calls `torrent-start-now`
    after fetching the list of torrents.
    """
    mock_network.side_effect = [
        success_response(),  # init
        success_response({"torrents": [{"id": 1, "queuePosition": 1, "hashString": "a"}]}),  # get_torrents
        success_response(),  # start
    ]
    c = Client()
    c.start_all(bypass_queue=True)

    # Verify the last call was torrent-start-now
    assert mock_network.call_count == 3
    last_call_json = mock_network.call_args_list[-1][1]["json"]
    assert last_call_json["method"] == "torrent-start-now"


def test_get_torrent_with_args(mock_network: Any, success_response: Any) -> None:
    """Verify that `get_torrent` raises KeyError if the requested fields are not returned by the server."""
    mock_network.side_effect = [
        success_response(),  # init
        success_response({"torrents": []}),  # get_torrent empty result
    ]
    c = Client()
    with pytest.raises(KeyError):
        c.get_torrent(1, arguments=["id", "name"])


def test_get_torrent_return_found(mock_network: Any, success_response: Any) -> None:
    """
    Verify logic to find and return the specific torrent in get_torrent.
    """
    mock_network.side_effect = [
        success_response(),
        success_response({"torrents": [{"id": 1, "hashString": "hash1", "name": "found"}]}),
    ]
    c = Client()
    t = c.get_torrent(1)
    assert t.id == 1
    assert t.name == "found"


def test_get_torrents_with_arguments(mock_network: Any, success_response: Any) -> None:
    """
    Verify argument set logic in get_torrents.
    """
    mock_network.side_effect = [success_response(), success_response({"torrents": []})]
    c = Client()
    # Passing arguments triggers the 'if arguments:' block
    c.get_torrents(arguments=["name", "id"])

    # Verify we sent the combined set of arguments
    sent_args = mock_network.call_args[1]["json"]["arguments"]["fields"]
    assert "name" in sent_args
    assert "hashString" in sent_args  # Added by the logic


def test_change_torrent_warnings_v1_protocol(mock_network: Any, success_response: Any) -> None:
    """Verify warnings are issued when using `change_torrent` features not supported by the current server version."""
    # Mock init to return version 1
    mock_network.side_effect = [
        mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "0"},
            data=json.dumps(
                {"result": "success", "arguments": {"rpc-version": 1, "version": "1.0", "rpc-version-semver": "1.0.0"}}
            ).encode(),
        ),
        success_response(),
        success_response(),
    ]

    c = Client()

    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.change_torrent(ids=1, tracker_list=[])
        mock_warn.assert_called()

    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.change_torrent(ids=1, group="g")
        mock_warn.assert_called()


def test_change_torrent_no_args(mock_network: Any, success_response: Any) -> None:
    """Verify that `change_torrent` raises ValueError if no arguments are provided."""
    mock_network.return_value = success_response()
    c = Client()
    with pytest.raises(ValueError, match="No arguments to set"):
        c.change_torrent(ids=1)


def test_set_session_warnings_full(mock_network: Any, success_response: Any) -> None:
    """Verify warnings are issued when using `set_session` features not supported by the current server version."""
    # Mock init to return version 1
    mock_network.side_effect = [
        mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "0"},
            data=json.dumps(
                {"result": "success", "arguments": {"rpc-version": 1, "version": "1.0", "rpc-version-semver": "1.0.0"}}
            ).encode(),
        ),
        success_response(),
        success_response(),
        success_response(),
        success_response(),
    ]

    c = Client()

    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.set_session(script_torrent_done_seeding_filename="f")
        mock_warn.assert_called()
    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.set_session(script_torrent_done_seeding_enabled=True)
        mock_warn.assert_called()
    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.set_session(script_torrent_added_enabled=True)
        mock_warn.assert_called()
    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.set_session(script_torrent_added_filename="f")
        mock_warn.assert_called()


def test_set_session_default_trackers(mock_network: Any, success_response: Any) -> None:
    """
    Verify warning trigger for default_trackers.
    """
    # Return rpc-version 16 so that default_trackers (req 17) triggers warning
    mock_network.return_value = success_response({"rpc-version": 16, "version": "3.00", "rpc-version-semver": "3.0.0"})
    c = Client()

    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.set_session(default_trackers=["http://tracker.com"])
        mock_warn.assert_called()


def test_set_group_warning(mock_network: Any, success_response: Any) -> None:
    """Verify warning is issued when using `set_group` on a server version that doesn't support it."""
    # Mock init to return version 1
    mock_network.side_effect = [
        mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "0"},
            data=json.dumps(
                {"result": "success", "arguments": {"rpc-version": 1, "version": "1.0", "rpc-version-semver": "1.0.0"}}
            ).encode(),
        ),
        success_response(),
    ]
    c = Client()

    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.set_group("g")
        mock_warn.assert_called()


def test_change_torrent_version_warnings(mock_network: Any, success_response: Any) -> None:
    """Verify specific warnings for `change_torrent` based on RPC version thresholds."""
    # We need to simulate different versions.
    # Case 1: Version 1 (low)
    mock_network.side_effect = [
        mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "0"},
            data=json.dumps(
                {"result": "success", "arguments": {"rpc-version": 1, "version": "1.0", "rpc-version-semver": "1.0.0"}}
            ).encode(),
        ),
        success_response(),
        success_response(),
        success_response(),
    ]
    c = Client()
    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.change_torrent(ids=1, labels=["a"])
        mock_warn.assert_called()  # v16 required

        c.change_torrent(ids=1, group="g")
        mock_warn.assert_called()  # v17 required

        c.change_torrent(ids=1, tracker_list=[["a"]])
        mock_warn.assert_called()  # v17 required


def test_group_operations(mock_network: Any, success_response: Any) -> None:
    """Cover `set_group` and `get_groups` functionality."""
    mock_network.side_effect = [
        success_response(),  # init
        success_response(),  # set_group
        success_response({"group": [{"name": "test_g"}]}),  # get_groups
        success_response({"group": [{"name": "test_g"}]}),  # get_group
        success_response({"group": []}),  # get_group missing
        success_response({"group": [{"name": "test_g"}]}),  # get_groups list
    ]

    c = Client()

    # Test set_group
    c.set_group("test_g")

    # Test get_groups
    groups = c.get_groups()
    assert "test_g" in groups

    # Test get_group
    g = c.get_group("test_g")
    assert g is not None
    assert g.name == "test_g"

    # Test get_group missing
    assert c.get_group("missing") is None

    # Test get_groups with list
    c.get_groups(["test_g"])
    assert mock_network.call_args[1]["json"]["arguments"]["group"] == ["test_g"]


def test_get_group_empty(mock_network: Any, success_response: Any) -> None:
    """Verify get_group returns None when result list is empty."""
    mock_network.side_effect = [
        success_response(),
        success_response({"group": []}),
    ]
    c = Client()
    assert c.get_group("missing") is None


def test_passthrough_rpc_commands(mock_network: Any, success_response: Any) -> None:
    """Verify execution of client command methods."""
    mock_network.side_effect = [
        success_response(),  # init
        # return a valid torrent for start_all to operate on
        success_response({"torrents": [{"id": 1, "queuePosition": 0, "hashString": "h"}]}),  # start_all (get)
        success_response(),  # start_all (start)
        success_response({"blocklist-size": 10}),  # blocklist
    ]
    c = Client()

    # start_all bypass_queue
    c.start_all(bypass_queue=True)

    # blocklist_update
    assert c.blocklist_update() == 10


def test_set_session_invalid_encryption_value(mock_network: Any, success_response: Any) -> None:
    """Verify that set_session raises ValueError when passed an invalid encryption mode string."""
    mock_network.return_value = success_response()
    c = Client()
    with pytest.raises(ValueError, match="Invalid encryption value"):
        c.set_session(encryption=cast("Any", "invalid"))


def test_start_torrent_bypass_queue_argument(mock_network: Any, success_response: Any) -> None:
    """Verify that start_torrent uses 'torrent-start-now' method when bypass_queue is True."""
    mock_network.return_value = success_response()
    c = Client()
    c.start_torrent(ids=1, bypass_queue=True)
    sent_json = mock_network.call_args[1]["json"]
    assert sent_json["method"] == "torrent-start-now"


def test_free_space_success_and_failure(mock_network: Any, success_response: Any) -> None:
    """Verify free_space returns size on success and None when paths do not match."""
    mock_network.return_value = success_response()
    c = Client()

    # Success case
    mock_network.return_value = success_response({"path": "/test/path", "size-bytes": 100})
    assert c.free_space("/test/path") == 100

    # Failure/Mismatch case
    mock_network.return_value = success_response({"path": "/other", "size-bytes": 0})
    assert c.free_space("/test/path") is None


def test_get_torrent_not_found(mock_network: Any, success_response: Any) -> None:
    """Verify that `get_torrent` raises KeyError if the returned list is empty."""
    mock_network.side_effect = [success_response(), success_response({"torrents": []})]
    c = Client()
    with pytest.raises(KeyError, match="Torrent not found"):
        c.get_torrent(1)


def test_session_stats_legacy(mock_network: Any, success_response: Any) -> None:
    """Verify `session_stats` compatibility with older response formats."""
    mock_network.side_effect = [
        success_response(),
        success_response(
            {
                "session-stats": {
                    "activeTorrentCount": 5,
                    "downloadSpeed": 1000,
                    "pausedTorrentCount": 0,
                    "torrentCount": 5,
                    "uploadSpeed": 1000,
                    "cumulative-stats": {},
                    "current-stats": {},
                }
            }
        ),
    ]
    c = Client()
    assert c.session_stats().active_torrent_count == 5


def test_session_stats_modern(mock_network: Any, success_response: Any) -> None:
    """Verify session_stats works when response is flat (modern)."""
    mock_network.side_effect = [
        success_response(),
        success_response(
            {
                "activeTorrentCount": 5,
                "downloadSpeed": 1000,
                "pausedTorrentCount": 0,
                "torrentCount": 5,
                "uploadSpeed": 1000,
                "cumulative-stats": {},
                "current-stats": {},
            }
        ),
    ]
    c = Client()
    stats = c.session_stats()
    assert stats.active_torrent_count == 5


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 protocol tests
# ---------------------------------------------------------------------------


def test_jsonrpc2_request_format_for_transmission_4_1() -> None:
    """
    Verify that the client automatically uses JSON-RPC 2.0 format (snake_case method
    name, ``params`` key, ``jsonrpc`` field) for Transmission 4.1.0+ servers.
    """
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        # Bootstrap: old-protocol response for the mandatory session-get in __init__
        mock_req.side_effect = [
            _jsonrpc2_init_response(),
            _jsonrpc2_response({"torrents": []}),
        ]
        c = Client()
        assert c._Client__use_jsonrpc2 is True  # type: ignore[attr-defined]
        c.get_torrents(arguments=["id", "hashString", "name"])

        sent = mock_req.call_args[1]["json"]
        assert sent.get("jsonrpc") == "2.0"
        assert sent.get("method") == "torrent_get", f"Expected snake_case method, got: {sent}"
        assert "params" in sent, "JSON-RPC 2.0 must use 'params', not 'arguments'"
        assert "hash_string" in sent["params"]["fields"], "Field names must be snake_case in JSON-RPC 2.0"


def test_jsonrpc2_old_protocol_unchanged_for_legacy_server(
    mock_network: Any, success_response: Any
) -> None:
    """
    Verify that the client continues to use the old bespoke protocol for servers
    with rpc-version < 18 (Transmission < 4.1.0).
    """
    mock_network.side_effect = [success_response(), success_response({"torrents": []})]
    c = Client()
    assert c._Client__use_jsonrpc2 is False  # type: ignore[attr-defined]
    c.get_torrents(arguments=["id", "hashString"])

    sent = mock_network.call_args[1]["json"]
    assert "jsonrpc" not in sent, "Old protocol must NOT include 'jsonrpc'"
    assert sent.get("method") == "torrent-get", "Old protocol must use hyphenated method names"
    assert "arguments" in sent, "Old protocol must use 'arguments', not 'params'"


def test_jsonrpc2_response_parsed_correctly() -> None:
    """
    Verify that a JSON-RPC 2.0 torrent response with snake_case field names is
    returned correctly and accessible via both snake_case and camelCase property names.
    """
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        mock_req.side_effect = [
            _jsonrpc2_init_response(),
            _jsonrpc2_response({"torrents": [{"id": 1, "hash_string": "abc" * 14, "name": "T"}]}),
        ]
        c = Client()
        torrents = c.get_torrents(arguments=["id", "hashString", "name"])

        assert len(torrents) == 1
        t = torrents[0]
        # The snake_case key from the JSON-RPC 2.0 response must be accessible via
        # the camelCase property accessor through _FieldDict key normalisation.
        assert t.fields.get("hash_string") == "abc" * 14
        assert t.name == "T"


def test_jsonrpc2_error_response_raises_transmission_error() -> None:
    """
    Verify that a JSON-RPC 2.0 error response (``"error"`` key) is translated into
    a ``TransmissionError`` whose message matches the server-provided text.
    """
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        error_resp = mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "sess"},
            data=json.dumps({
                "jsonrpc": "2.0",
                "error": {"code": -32600, "message": "Invalid params"},
                "id": 2,
            }).encode(),
        )
        mock_req.side_effect = [_jsonrpc2_init_response(), error_resp]
        c = Client()
        with pytest.raises(TransmissionError, match="Invalid params"):
            c.get_torrents()


def test_jsonrpc2_torrent_add_snake_case_response() -> None:
    """
    Verify that a JSON-RPC 2.0 ``torrent_add`` response that uses ``torrent_added``
    (snake_case) is handled correctly and returns a valid ``Torrent`` object.
    """
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        add_resp = _jsonrpc2_response(
            {"torrent_added": {"id": 42, "hash_string": "abc" * 14, "name": "New"}}
        )
        mock_req.side_effect = [_jsonrpc2_init_response(), add_resp]
        c = Client()
        t = c.add_torrent("magnet:?xt=urn:btih:abc")
        assert t.id == 42
        assert t.name == "New"


def test_jsonrpc2_409_header_detection_switches_protocol() -> None:
    """
    Verify that the ``X-Transmission-Rpc-Version`` header in a CSRF 409 response
    is used to detect JSON-RPC 2.0 support, and that the *retry* of that same
    request is sent in JSON-RPC 2.0 format (not the old bespoke format).
    """
    response_409 = mock.Mock(
        status=409,
        headers={
            "x-transmission-session-id": "new_sess",
            "x-transmission-rpc-version": "6.0.0",
        },
        data=b"",
    )
    # The retry after 409 uses JSON-RPC 2.0; server echoes the new protocol back.
    response_ok = mock.Mock(
        status=200,
        headers={"x-transmission-session-id": "new_sess"},
        data=json.dumps({
            "jsonrpc": "2.0",
            "result": {"rpc_version": 18, "rpc_version_semver": "6.0.0", "version": "4.1.0"},
            "id": 1,
        }).encode(),
    )

    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        mock_req.side_effect = [response_409, response_ok]
        c = Client()

        # The flag must have been set during 409 processing.
        assert c._Client__use_jsonrpc2 is True  # type: ignore[attr-defined]

        # The *second* HTTP call (the retry after 409) must be in JSON-RPC 2.0 format.
        retry_call = mock_req.call_args_list[1]
        sent = retry_call[1]["json"]
        assert sent.get("jsonrpc") == "2.0", f"Retry after 409 must use JSON-RPC 2.0, got: {sent}"
        assert sent.get("method") == "session_get", f"Method must be snake_case: {sent}"
