from typing import Any, cast
from unittest import mock

import pytest

from transmission_rpc.client import Client
from transmission_rpc.torrent import Torrent


@pytest.mark.parametrize(
    ("method_name", "expected_method"),
    [("start_torrent", "torrent_start"), ("start_torrent_now", "torrent_start_now")],
)
def test_start_methods_use_all_torrents_by_default(
    mock_network: Any,
    success_response: Any,
    method_name: str,
    expected_method: str,
) -> None:
    """Verify that each start method omits ids by default, applying its action to all torrents."""
    mock_network.side_effect = [
        success_response(),  # init
        success_response(),  # start
    ]
    c = Client()
    assert getattr(c, method_name)() is None

    assert mock_network.call_count == 2
    last_call_json = mock_network.call_args_list[-1][1]["json"]
    assert last_call_json["jsonrpc"] == "2.0"
    assert last_call_json["method"] == expected_method
    assert last_call_json["params"] == {}


@pytest.mark.parametrize(
    ("method_name", "expected_method"),
    [("start_torrent", "torrent_start"), ("start_torrent_now", "torrent_start_now")],
)
@pytest.mark.parametrize(
    ("ids", "expected_arguments"),
    [(None, {}), ([], {}), (1, {"ids": [1]})],
)
def test_start_methods_pass_torrent_ids(
    mock_network: Any,
    success_response: Any,
    method_name: str,
    expected_method: str,
    ids: Any,
    expected_arguments: dict[str, Any],
) -> None:
    """Verify that start actions omit empty ids and pass explicit ids to Transmission."""
    mock_network.return_value = success_response()
    c = Client()
    assert getattr(c, method_name)(ids=ids) is None

    sent_json = mock_network.call_args_list[-1][1]["json"]
    assert sent_json["jsonrpc"] == "2.0"
    assert sent_json["method"] == expected_method
    assert sent_json["params"] == expected_arguments


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
        success_response({"torrents": [{"id": 1, "hash_string": "hash1", "name": "found"}]}),
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
    sent_args = mock_network.call_args[1]["json"]["params"]["fields"]
    assert "name" in sent_args
    assert "hash_string" in sent_args  # Added by the logic


def test_change_torrent_warnings_v1_protocol(mock_network: Any, legacy_response: Any) -> None:
    """Verify warnings are issued when using `change_torrent` features not supported by the current server version."""
    # Mock a pre-4.1.0 server: the initial JSON-RPC probe falls back to legacy
    # and the request is resent once.
    mock_network.side_effect = [
        legacy_response({"rpc-version": 1, "version": "1.0", "rpc-version-semver": "1.0.0"}),  # init probe
        legacy_response({"rpc-version": 1, "version": "1.0", "rpc-version-semver": "1.0.0"}),  # init legacy retry
        legacy_response(),  # change_torrent tracker_list
        legacy_response(),  # change_torrent group
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


def test_change_torrent_round_trips_tracker_tiers(mock_network: Any, success_response: Any) -> None:
    mock_network.side_effect = [success_response(), success_response()]
    client = Client()
    torrent = Torrent(
        fields={
            "id": 1,
            "tracker_list": (
                "https://a.example/announce\nhttps://b.example/announce\n\nhttps://backup.example/announce\n"
            ),
        }
    )

    client.change_torrent(ids=torrent.id, tracker_list=torrent.tracker_list)

    sent = mock_network.call_args.kwargs["json"]["params"]["tracker_list"]
    assert sent == ("https://a.example/announce\nhttps://b.example/announce\n\nhttps://backup.example/announce")


def test_change_torrent_rejects_flat_tracker_list_before_request(mock_network: Any, success_response: Any) -> None:
    mock_network.return_value = success_response()
    client = Client()
    calls_before = mock_network.call_count

    with pytest.raises(TypeError, match="contain tracker tiers"):
        client.change_torrent(ids=1, tracker_list=["https://tracker.example/announce"])  # type: ignore[list-item]

    assert mock_network.call_count == calls_before


def test_set_session_warnings_full(mock_network: Any, legacy_response: Any) -> None:
    """Verify warnings are issued when using `set_session` features not supported by the current server version."""
    # Mock init to return version 1
    mock_network.side_effect = [
        legacy_response({"rpc-version": 1, "version": "1.0", "rpc-version-semver": "1.0.0"}),  # init probe
        legacy_response({"rpc-version": 1, "version": "1.0", "rpc-version-semver": "1.0.0"}),  # init legacy retry
        legacy_response(),  # set_session 1
        legacy_response(),  # set_session 2
        legacy_response(),  # set_session 3
        legacy_response(),  # set_session 4
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


def test_set_session_default_trackers(mock_network: Any, legacy_response: Any) -> None:
    """
    Verify warning trigger for default_trackers.
    """
    # Return rpc-version 16 so that default_trackers (req 17) triggers warning
    mock_network.return_value = legacy_response({"rpc-version": 16, "version": "3.00", "rpc-version-semver": "3.0.0"})
    c = Client()

    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.set_session(default_trackers=["http://tracker.com"])
        mock_warn.assert_called()


def test_set_group_warning(mock_network: Any, legacy_response: Any) -> None:
    """Verify warning is issued when using `set_group` on a server version that doesn't support it."""
    # Mock init to return version 1
    mock_network.side_effect = [
        legacy_response({"rpc-version": 1, "version": "1.0", "rpc-version-semver": "1.0.0"}),  # init probe
        legacy_response({"rpc-version": 1, "version": "1.0", "rpc-version-semver": "1.0.0"}),  # init legacy retry
        legacy_response(),  # set_group
    ]
    c = Client()

    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.set_group("g")
        mock_warn.assert_called()


def test_change_torrent_version_warnings(mock_network: Any, legacy_response: Any) -> None:
    """Verify specific warnings for `change_torrent` based on RPC version thresholds."""
    # We need to simulate different versions.
    # Case 1: Version 1 (low)
    mock_network.side_effect = [
        legacy_response({"rpc-version": 1, "version": "1.0", "rpc-version-semver": "1.0.0"}),  # init probe
        legacy_response({"rpc-version": 1, "version": "1.0", "rpc-version-semver": "1.0.0"}),  # init legacy retry
        legacy_response(),  # change_torrent labels
        legacy_response(),  # change_torrent group
        legacy_response(),  # change_torrent tracker_list
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
    assert mock_network.call_args[1]["json"]["params"]["group"] == ["test_g"]


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
        success_response(),  # start_torrent_now
        success_response({"blocklist_size": 10}),  # blocklist
    ]
    c = Client()

    # start_torrent_now
    c.start_torrent_now()

    # blocklist_update
    assert c.blocklist_update() == 10


def test_set_session_invalid_encryption_value(mock_network: Any, success_response: Any) -> None:
    """Verify that set_session raises ValueError when passed an invalid encryption mode string."""
    mock_network.return_value = success_response()
    c = Client()
    with pytest.raises(ValueError, match="Invalid encryption value"):
        c.set_session(encryption=cast("Any", "invalid"))


def test_free_space_success_and_failure(mock_network: Any, success_response: Any) -> None:
    """Verify free_space returns size on success and None when paths do not match."""
    mock_network.return_value = success_response()
    c = Client()

    # Success case
    mock_network.return_value = success_response({"path": "/test/path", "size_bytes": 100})
    assert c.free_space("/test/path") == 100

    # Failure/Mismatch case
    mock_network.return_value = success_response({"path": "/other", "size_bytes": 0})
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
                "session_stats": {
                    "active_torrent_count": 5,
                    "download_speed": 1000,
                    "paused_torrent_count": 0,
                    "torrent_count": 5,
                    "upload_speed": 1000,
                    "cumulative_stats": {},
                    "current_stats": {},
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
                "active_torrent_count": 5,
                "download_speed": 1000,
                "paused_torrent_count": 0,
                "torrent_count": 5,
                "upload_speed": 1000,
                "cumulative_stats": {},
                "current_stats": {},
            }
        ),
    ]
    c = Client()
    stats = c.session_stats()
    assert stats.active_torrent_count == 5
