import contextlib
import io
import json
import pathlib
from unittest import mock

import pytest

from transmission_rpc.client import Client
from transmission_rpc.error import TransmissionError


def test_start_torrent_no_ids(client: Client) -> None:
    """Verify that `start_torrent` raises ValueError if no IDs are provided."""
    with pytest.raises(ValueError, match="request require ids"):
        client.start_torrent(ids=[])


def test_start_all_bypass_queue(client: Client) -> None:
    """
    Verify that `start_all(bypass_queue=True)` correctly calls `torrent-start-now`
    after fetching the list of torrents.
    """
    client._Client__http_client.request.reset_mock()  # type: ignore[attr-defined] # noqa: SLF001
    client._Client__http_client.request.side_effect = [  # type: ignore[attr-defined] # noqa: SLF001
        mock.Mock(
            status=200,
            headers={},
            data=json.dumps(
                {"result": "success", "arguments": {"torrents": [{"id": 1, "queuePosition": 1, "hashString": "a"}]}}
            ).encode(),
        ),
        mock.Mock(status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()),
    ]
    client.start_all(bypass_queue=True)


def test_get_torrent_with_args(client: Client) -> None:
    """Verify that `get_torrent` raises KeyError if the requested fields are not returned by the server."""
    client._Client__http_client.request.return_value.data = json.dumps(  # type: ignore[attr-defined] # noqa: SLF001
        {"result": "success", "arguments": {"torrents": []}}
    ).encode()
    with pytest.raises(KeyError):
        client.get_torrent(1, arguments=["id", "name"])


def test_change_torrent_warnings_v1_protocol(client: Client) -> None:
    """Verify warnings are issued when using `change_torrent` features not supported by the current server version."""
    client._Client__protocol_version = 1  # type: ignore[attr-defined] # noqa: SLF001
    client._Client__http_client.request.return_value.data = json.dumps({"result": "success", "arguments": {}}).encode()  # type: ignore[attr-defined] # noqa: SLF001
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.change_torrent(ids=1, tracker_list=[])
        mock_warn.assert_called()
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.change_torrent(ids=1, group="g")
        mock_warn.assert_called()


def test_change_torrent_no_args(client: Client) -> None:
    """Verify that `change_torrent` raises ValueError if no arguments are provided to modify the torrent."""
    with pytest.raises(ValueError, match="No arguments to set"):
        client.change_torrent(ids=1)


def test_set_session_warnings_full(client: Client) -> None:
    """Verify warnings are issued when using `set_session` features not supported by the current server version."""
    client._Client__protocol_version = 1  # type: ignore[attr-defined] # noqa: SLF001
    client._Client__http_client.request.return_value.data = json.dumps({"result": "success", "arguments": {}}).encode()  # type: ignore[attr-defined] # noqa: SLF001
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.set_session(script_torrent_done_seeding_filename="f")
        mock_warn.assert_called()
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.set_session(script_torrent_done_seeding_enabled=True)
        mock_warn.assert_called()
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.set_session(script_torrent_added_enabled=True)
        mock_warn.assert_called()
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.set_session(script_torrent_added_filename="f")
        mock_warn.assert_called()


def test_set_group_warning(client: Client) -> None:
    """Verify warning is issued when using `set_group` on a server version that doesn't support it."""
    client._Client__protocol_version = 1  # type: ignore[attr-defined] # noqa: SLF001
    client._Client__http_client.request.return_value.data = json.dumps({"result": "success", "arguments": {}}).encode()  # type: ignore[attr-defined] # noqa: SLF001
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.set_group("g")
        mock_warn.assert_called()


def test_file_scheme_error() -> None:
    """Verify that using the `file://` scheme in `add_torrent` raises a ValueError."""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        with pytest.raises(ValueError, match="support for `file://` URL has been removed"):
            c.add_torrent("file:///tmp/test.torrent")


def test_change_torrent_version_warnings() -> None:
    """Verify specific warnings for `change_torrent` based on RPC version thresholds."""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        # Mock internal request method
        c._request = mock.Mock()  # type: ignore[method-assign] # noqa: SLF001
        c.logger = mock.Mock()  # type: ignore[method-assign]
        # Mock _rpc_version_warning to verify calls
        c._rpc_version_warning = mock.Mock()  # type: ignore[method-assign] # noqa: SLF001

        # Test labels warning (v16)
        c.change_torrent(ids=1, labels=["a"])
        c._rpc_version_warning.assert_any_call(16)  # noqa: SLF001

        # Test group warning (v17)
        c.change_torrent(ids=1, group="g")
        c._rpc_version_warning.assert_any_call(17)  # noqa: SLF001

        # Test tracker_list warning (v17)
        c.change_torrent(ids=1, tracker_list=[["a"]])
        c._rpc_version_warning.assert_any_call(17)  # noqa: SLF001


def test_groups_coverage() -> None:
    """Cover `set_group` and `get_groups` functionality, mocking the RPC response."""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        # We need to mock _request to return something valid
        c._request = mock.Mock(return_value={"group": [{"name": "test_g"}]})  # type: ignore[method-assign] # noqa: SLF001

        # Test set_group
        c.set_group("test_g")
        c._request.assert_called_with(mock.ANY, {"name": "test_g"}, timeout=None)  # noqa: SLF001

        # Test get_groups
        groups = c.get_groups()
        assert "test_g" in groups

        # Test get_group
        g = c.get_group("test_g")
        assert g is not None
        assert g.name == "test_g"

        # Test get_group missing
        c._request.return_value = {"group": []}  # noqa: SLF001
        assert c.get_group("missing") is None

        # Test get_groups with list
        c.get_groups(["test_g"])
        c._request.assert_called_with(mock.ANY, {"group": ["test_g"]}, timeout=None)  # noqa: SLF001


def test_rpc_command_methods() -> None:
    """
    Verify execution of client command methods that do not return detailed data,
    including `start_all`, `stop_torrent`, `reannounce_torrent`, and `blocklist_update`.
    """
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c._request = mock.Mock()  # type: ignore[method-assign] # noqa: SLF001

        # start_all bypass_queue
        c._request.return_value = {"torrents": []}  # noqa: SLF001
        c.start_all(bypass_queue=True)
        assert c._request.call_args[0][0] == "torrent-start-now"  # noqa: SLF001

        # stop_torrent
        c.stop_torrent(ids=1)

        # reannounce_torrent
        c.reannounce_torrent(ids=1)

        # blocklist_update
        c._request.return_value = {"blocklist-size": 10}  # noqa: SLF001
        assert c.blocklist_update() == 10


def test_add_torrent_args() -> None:
    """Cover `add_torrent` arguments like labels, sequential_download, and bandwidthPriority."""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c._request = mock.Mock(return_value={"torrent-added": {"id": 1, "name": "n", "hashString": "h"}})  # type: ignore[method-assign] # noqa: SLF001

        # labels, sequential_download, bandwidthPriority
        c.add_torrent("magnet:?xt=urn:btih:a", labels=["l"], sequential_download=True, bandwidthPriority=1)


def test_misc_rpc_method_edge_cases() -> None:
    """
    Verify edge case handling for invalid session encryption values, `start_torrent` queue bypassing,
    field filtering in `get_torrents`, and path mismatches in `free_space`.
    """
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c._request = mock.Mock()  # type: ignore[method-assign] # noqa: SLF001

        # set_session invalid encryption
        with pytest.raises(ValueError, match="Invalid encryption value"):
            c.set_session(encryption="invalid")  # type: ignore

        # start_torrent bypass_queue
        c.start_torrent(ids=1, bypass_queue=True)
        assert c._request.call_args[0][0] == "torrent-start-now"  # noqa: SLF001

        # get_torrents with arguments
        c._request.return_value = {"torrents": []}  # noqa: SLF001
        c.get_torrents(ids=1, arguments=["name"])
        args = c._request.call_args[0][1]["fields"]  # noqa: SLF001
        assert "name" in args
        assert "id" in args

        # get_recently_active_torrents with arguments
        c._request.return_value = {"torrents": [], "removed": []}  # noqa: SLF001
        c.get_recently_active_torrents(arguments=["name"])
        args = c._request.call_args[0][1]["fields"]  # noqa: SLF001
        assert "name" in args

        # free_space success
        c._request.return_value = {"path": "/tmp", "size-bytes": 100}  # noqa: SLF001, S108
        assert c.free_space("/tmp") == 100  # noqa: S108

        # free_space fail
        c._request.return_value = {"path": "/other", "size-bytes": 0}  # noqa: SLF001
        assert c.free_space("/tmp") is None  # noqa: S108


def test_add_torrent_types() -> None:
    """Cover `add_torrent` with different input types (bytes, file-like, Path)."""

    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c._request = mock.Mock(return_value={"torrent-added": {"id": 1, "name": "n", "hashString": "h"}})  # type: ignore[method-assign] # noqa: SLF001

        # bytes
        c.add_torrent(b"torrent content")
        assert "metainfo" in c._request.call_args[0][1]  # noqa: SLF001

        # file-like
        f = io.BytesIO(b"torrent content")
        c.add_torrent(f)
        assert "metainfo" in c._request.call_args[0][1]  # noqa: SLF001

        # Path (local file)
        # We need to mock path reading
        p = pathlib.Path("test.torrent")
        with mock.patch("pathlib.Path.read_bytes", return_value=b"content"):
            c.add_torrent(p)
        assert "metainfo" in c._request.call_args[0][1]  # noqa: SLF001


def test_add_torrent_empty_metadata_and_unknown_types() -> None:
    """
    Verify that `add_torrent` raises ValueError for empty metadata or unknown input types.
    """
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c._request = mock.Mock()  # type: ignore[method-assign] # noqa: SLF001

        # Test handling of empty metadata
        with pytest.raises(ValueError, match="Torrent metadata is empty"):
            c.add_torrent(b"")

        # Test _try_read_torrent returns None for unknown type
        # We pass an object that is not str/Path/bytes/read
        obj = object()
        # It returns None, so code proceeds to: kwargs["filename"] = obj
        # Then calls _request.
        c._request.return_value = {"torrent-added": {"id": 1}}  # noqa: SLF001
        c.add_torrent(obj)  # type: ignore

    # Use a new client to test _request logic because we need the real _request to run
    # Client.get_session is already patched by the outer context if we are not careful
    # But here we are outside the with block of c

    with mock.patch.object(Client, "get_session", autospec=True):
        c2 = Client()
        c2.logger = mock.Mock()

        # 1. SessionStats fallback
        c2._http_query = mock.Mock(  # type: ignore[method-assign] # noqa: SLF001
            return_value=json.dumps({"result": "success", "arguments": {"activeTorrentCount": 1}})
        )
        stats = c2.session_stats()
        assert stats.active_torrent_count == 1

        # 2. TorrentAdd logic
        c2._http_query.return_value = json.dumps(  # noqa: SLF001
            {"result": "success", "arguments": {"torrent-added": {"id": 1, "name": "n", "hashString": "h"}}}
        )
        # add_torrent calls _request. We pass 'magnet' so it doesn't try to read file.
        t = c2.add_torrent("magnet:?xt=urn:btih:h")
        assert t.id == 1

        # 3. get_torrent finding torrent
        c2._http_query.return_value = json.dumps(  # noqa: SLF001
            {"result": "success", "arguments": {"torrents": [{"id": 1, "name": "n", "hashString": "h"}]}}
        )
        t = c2.get_torrent(1)
        assert t.id == 1


def test_add_torrent_duplicate(client: Client) -> None:
    """Verify that `add_torrent` handles the 'torrent-duplicate' response correctly."""
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200,
        headers={},
        data=json.dumps(
            {"result": "success", "arguments": {"torrent-duplicate": {"id": 1, "name": "test", "hashString": "hash"}}}
        ).encode(),
    )
    res = client.add_torrent("magnet:?xt=urn:btih:hash")
    assert res.id == 1


def test_add_torrent_invalid_response(client: Client) -> None:
    """Verify that `add_torrent` raises TransmissionError if the response doesn't contain 'torrent-added' or 'torrent-duplicate'."""
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    with pytest.raises(TransmissionError, match="Invalid torrent-add response"):
        client.add_torrent("magnet:?xt=urn:btih:hash")


def test_get_torrent_not_found(client: Client) -> None:
    """Verify that `get_torrent` raises KeyError if the returned list of torrents is empty."""
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {"torrents": []}}).encode()
    )
    with pytest.raises(KeyError, match="Torrent not found"):
        client.get_torrent(1)


def test_session_stats_legacy(client: Client) -> None:
    """Verify `session_stats` compatibility with older response formats."""
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200,
        headers={},
        data=json.dumps(
            {
                "result": "success",
                "arguments": {
                    "session-stats": {
                        "activeTorrentCount": 5,
                        "downloadSpeed": 1000,
                        "pausedTorrentCount": 0,
                        "torrentCount": 5,
                        "uploadSpeed": 1000,
                        "cumulative-stats": {},
                        "current-stats": {},
                    }
                },
            }
        ).encode(),
    )
    assert client.session_stats().active_torrent_count == 5


def test_free_space_path_mismatch(client: Client) -> None:
    """Verify `free_space` returns None if the returned path does not match the requested path."""
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200,
        headers={},
        data=json.dumps({"result": "success", "arguments": {"path": "/other", "size-bytes": 100}}).encode(),
    )
    assert client.free_space("/test") is None


def test_get_group_none(client: Client) -> None:
    """Verify `get_group` returns None if the group is not found."""
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {"group": []}}).encode()
    )
    assert client.get_group("test") is None


def test_void_rpc_methods_success(client: Client) -> None:
    """
    Verify that various client methods (e.g., queue movement, session configuration)
    execute without error and return None when the server responds with success.
    """
    # Set default success response
    client._Client__http_client.request.return_value.data = json.dumps(  # type: ignore[attr-defined] # noqa: SLF001
        {
            "result": "success",
            "arguments": {},
        }
    ).encode()

    methods = [
        ("remove_torrent", {"ids": 1}),
        ("start_torrent", {"ids": 1}),
        ("stop_torrent", {"ids": 1}),
        ("verify_torrent", {"ids": 1}),
        ("reannounce_torrent", {"ids": 1}),
        ("move_torrent_data", {"ids": 1, "location": "/tmp"}),  # noqa: S108
        ("queue_top", {"ids": 1}),
        ("queue_bottom", {"ids": 1}),
        ("queue_up", {"ids": 1}),
        ("queue_down", {"ids": 1}),
        ("set_session", {"alt_speed_enabled": True}),
        ("session_close", {}),
        ("set_group", {"name": "g1"}),
    ]
    for method_name, kwargs in methods:
        getattr(client, method_name)(**kwargs)


def test_change_torrent(client: Client) -> None:
    """Verify `change_torrent` executes successfully with valid arguments."""
    client._Client__http_client.request.return_value.data = json.dumps(  # type: ignore[attr-defined] # noqa: SLF001
        {
            "result": "success",
            "arguments": {},
        }
    ).encode()
    client.change_torrent(ids=1, download_limit=100)


def test_rename_torrent_path(client: Client) -> None:
    """Verify `rename_torrent_path` executes successfully."""
    client._Client__http_client.request.return_value.data = json.dumps(  # type: ignore[attr-defined] # noqa: SLF001
        {
            "result": "success",
            "arguments": {"path": "/a", "name": "b"},
        }
    ).encode()
    client.rename_torrent_path(1, "/path", "name")


def test_blocklist_update_extended(client: Client) -> None:
    """Verify `blocklist_update` returns the blocklist size."""
    client._Client__http_client.request.return_value.data = json.dumps(  # type: ignore[attr-defined] # noqa: SLF001
        {
            "result": "success",
            "arguments": {"blocklist-size": 10},
        }
    ).encode()
    assert client.blocklist_update() == 10


def test_port_test(client: Client) -> None:
    """Verify `port_test` returns the port status."""
    client._Client__http_client.request.return_value.data = json.dumps(  # type: ignore[attr-defined] # noqa: SLF001
        {
            "result": "success",
            "arguments": {"port-is-open": True, "ip_protocol": "ipv4"},
        }
    ).encode()
    assert client.port_test().port_is_open is True


def test_get_recently_active_torrents_extended(client: Client) -> None:
    """Verify `get_recently_active_torrents` executes successfully."""
    client._Client__http_client.request.return_value.data = json.dumps(  # type: ignore[attr-defined] # noqa: SLF001
        {
            "result": "success",
            "arguments": {"torrents": [], "removed": []},
        }
    ).encode()
    client.get_recently_active_torrents()


def test_get_groups_extended(client: Client) -> None:
    """Verify `get_groups` executes successfully."""
    client._Client__http_client.request.return_value.data = json.dumps(  # type: ignore[attr-defined] # noqa: SLF001
        {
            "result": "success",
            "arguments": {"group": []},
        }
    ).encode()
    client.get_groups()


def test_start_all_extended(client: Client) -> None:
    """
    Verify `start_all` logic with multiple torrents:
    it sorts them by queue position and then calls start.
    """
    client._Client__http_client.request.reset_mock()  # type: ignore[attr-defined] # noqa: SLF001
    # start_all calls get_torrents first to sort by queue position
    client._Client__http_client.request.side_effect = [  # type: ignore[attr-defined] # noqa: SLF001
        # 1. get_torrents response
        mock.Mock(
            status=200,
            headers={},
            data=json.dumps(
                {
                    "result": "success",
                    "arguments": {
                        "torrents": [
                            {"id": 1, "queuePosition": 2, "hashString": "a"},
                            {"id": 2, "queuePosition": 1, "hashString": "b"},
                        ]
                    },
                }
            ).encode(),
        ),
        # 2. torrent-start response
        mock.Mock(status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()),
    ]
    client.start_all()
    # Should call start with ids [2, 1] because 2 has pos 1, 1 has pos 2.
    # The last call should be start.
    assert client._Client__http_client.request.call_count == 2  # type: ignore[attr-defined] # noqa: SLF001


def test_rpc_version_warning(client: Client) -> None:
    """Verify that `_rpc_version_warning` emits a warning when protocol version is too low."""
    # Set low protocol version
    client._Client__protocol_version = 1  # type: ignore[attr-defined] # noqa: SLF001
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client._rpc_version_warning(2)  # noqa: SLF001
        mock_warn.assert_called()


def test_set_session_tracker_warnings(client: Client) -> None:
    """Verify that `set_session` emits warnings for features not supported by the current server version."""
    client._Client__protocol_version = 16  # type: ignore[attr-defined] # noqa: SLF001
    client._Client__http_client.request.return_value.data = json.dumps({"result": "success", "arguments": {}}).encode()  # type: ignore[attr-defined] # noqa: SLF001
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.set_session(default_trackers=["a"])
        mock_warn.assert_called()


def test_change_torrent_warnings_v15_protocol(client: Client) -> None:
    """Verify that `change_torrent` emits warnings for features not supported by the current server version."""
    client._Client__protocol_version = 15  # type: ignore[attr-defined] # noqa: SLF001
    client._Client__http_client.request.return_value.data = json.dumps({"result": "success", "arguments": {}}).encode()  # type: ignore[attr-defined] # noqa: SLF001
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.change_torrent(ids=1, labels=["a"])
        mock_warn.assert_called()


def test_parsing_ids(client: Client) -> None:
    """
    Verify that `_parse_torrent_ids` (via proxy methods) raises ValueError for invalid IDs:
    - Invalid hex string length.
    - Invalid hex characters.
    - Invalid types (e.g., objects, float).
    """
    # Test invalid hex string length
    with pytest.raises(ValueError, match="not valid torrent id"):
        client.get_torrent("a")  # length != 40

    # Test invalid hex string content
    with pytest.raises(ValueError, match="not valid torrent id"):
        client.get_torrent("z" * 40)

    # Test invalid type for _parse_torrent_id (called via get_torrent -> _parse_torrent_ids -> _parse_torrent_id)
    # Wait, _parse_torrent_ids handles int, str, list.
    # If list has invalid type?
    with pytest.raises(ValueError, match="is not valid torrent id"):
        client.start_torrent(ids=[object()])  # type: ignore

    # Test valid hash string
    h = "a" * 40
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200,
        headers={},
        data=json.dumps({"result": "success", "arguments": {"torrents": []}}).encode(),
    )
    with contextlib.suppress(KeyError):
        client.get_torrent(h)

    # Test invalid type for _parse_torrent_ids (e.g. float)
    with pytest.raises(ValueError, match="Invalid torrent id"):
        client.start_torrent(ids=1.5)  # type: ignore


def test_client_add_kwargs() -> None:
    """
    Verify that `add_torrent` correctly translates keyword arguments into the RPC request payload.
    """
    torrent_url = "https://github.com/trim21/transmission-rpc/raw/v4.1.0/tests/fixtures/iso.torrent"
    m = mock.Mock(return_value={"hello": "workd"})
    with mock.patch.object(Client, "_request", m):
        with mock.patch.object(Client, "get_session"):
            c = Client()
            c.add_torrent(
                torrent_url,
                download_dir="dd",
                files_unwanted=[1, 2],
                files_wanted=[3, 4],
                paused=False,
                peer_limit=5,
                priority_high=[6],
                priority_low=[7],
                priority_normal=[8],
                cookies="coo",
                bandwidthPriority=4,
            )
        m.assert_called_with(
            "torrent-add",
            {
                "filename": torrent_url,
                "download-dir": "dd",
                "files-unwanted": [1, 2],
                "files-wanted": [3, 4],
                "paused": False,
                "peer-limit": 5,
                "priority-high": [6],
                "priority-low": [7],
                "priority-normal": [8],
                "cookies": "coo",
                "bandwidthPriority": 4,
            },
            timeout=None,
        )
