# ruff: noqa: SLF001, S108
import contextlib
import io
import json
import pathlib
from unittest import mock

import pytest

from transmission_rpc.client import Client
from transmission_rpc.error import TransmissionError


def test_start_torrent_no_ids(client: Client) -> None:
    with pytest.raises(ValueError, match="request require ids"):
        client.start_torrent(ids=[])


def test_start_all_bypass_queue(client: Client) -> None:
    client._Client__http_client.request.reset_mock()  # type: ignore[attr-defined]
    client._Client__http_client.request.side_effect = [  # type: ignore[attr-defined]
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
    client._Client__http_client.request.return_value.data = json.dumps(  # type: ignore[attr-defined]
        {"result": "success", "arguments": {"torrents": []}}
    ).encode()
    with pytest.raises(KeyError):
        client.get_torrent(1, arguments=["id", "name"])


def test_change_torrent_warnings_full(client: Client) -> None:
    client._Client__protocol_version = 1  # type: ignore[attr-defined]
    client._Client__http_client.request.return_value.data = json.dumps({"result": "success", "arguments": {}}).encode()  # type: ignore[attr-defined]
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.change_torrent(ids=1, tracker_list=[])
        mock_warn.assert_called()
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.change_torrent(ids=1, group="g")
        mock_warn.assert_called()


def test_change_torrent_no_args(client: Client) -> None:
    with pytest.raises(ValueError, match="No arguments to set"):
        client.change_torrent(ids=1)


def test_set_session_warnings_full(client: Client) -> None:
    client._Client__protocol_version = 1  # type: ignore[attr-defined]
    client._Client__http_client.request.return_value.data = json.dumps({"result": "success", "arguments": {}}).encode()  # type: ignore[attr-defined]
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
    client._Client__protocol_version = 1  # type: ignore[attr-defined]
    client._Client__http_client.request.return_value.data = json.dumps({"result": "success", "arguments": {}}).encode()  # type: ignore[attr-defined]
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.set_group("g")
        mock_warn.assert_called()


def test_file_scheme_error() -> None:
    """Cover usage of file:// scheme error"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        with pytest.raises(ValueError, match="support for `file://` URL has been removed"):
            c.add_torrent("file:///tmp/test.torrent")


def test_change_torrent_warnings() -> None:
    """Cover warnings for new RPC features"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        # Mock internal request method
        c._request = mock.Mock()  # type: ignore[method-assign]
        c.logger = mock.Mock()  # type: ignore[method-assign]
        # Mock _rpc_version_warning to verify calls
        c._rpc_version_warning = mock.Mock()  # type: ignore[method-assign]

        # Test labels warning (v16)
        c.change_torrent(ids=1, labels=["a"])
        c._rpc_version_warning.assert_any_call(16)

        # Test group warning (v17)
        c.change_torrent(ids=1, group="g")
        c._rpc_version_warning.assert_any_call(17)

        # Test tracker_list warning (v17)
        c.change_torrent(ids=1, tracker_list=[["a"]])
        c._rpc_version_warning.assert_any_call(17)


def test_groups_coverage() -> None:
    """Cover set_group and get_groups which are skipped on older servers"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        # We need to mock _request to return something valid
        c._request = mock.Mock(return_value={"group": [{"name": "test_g"}]})  # type: ignore[method-assign]

        # Test set_group
        c.set_group("test_g")
        c._request.assert_called_with(mock.ANY, {"name": "test_g"}, timeout=None)

        # Test get_groups
        groups = c.get_groups()
        assert "test_g" in groups

        # Test get_group
        g = c.get_group("test_g")
        assert g is not None
        assert g.name == "test_g"

        # Test get_group missing
        c._request.return_value = {"group": []}
        assert c.get_group("missing") is None

        # Test get_groups with list
        c.get_groups(["test_g"])
        c._request.assert_called_with(mock.ANY, {"group": ["test_g"]}, timeout=None)


def test_more_client_methods_rpc() -> None:
    """Cover remaining client methods (RPC parts)"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c._request = mock.Mock()  # type: ignore[method-assign]

        # start_all bypass_queue
        c._request.return_value = {"torrents": []}
        c.start_all(bypass_queue=True)
        assert c._request.call_args[0][0] == "torrent-start-now"

        # stop_torrent
        c.stop_torrent(ids=1)

        # reannounce_torrent
        c.reannounce_torrent(ids=1)

        # blocklist_update
        c._request.return_value = {"blocklist-size": 10}
        assert c.blocklist_update() == 10


def test_add_torrent_args() -> None:
    """Cover add_torrent args"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c._request = mock.Mock(return_value={"torrent-added": {"id": 1, "name": "n", "hashString": "h"}})  # type: ignore[method-assign]

        # labels, sequential_download, bandwidthPriority
        c.add_torrent("magnet:?xt=urn:btih:a", labels=["l"], sequential_download=True, bandwidthPriority=1)


def test_even_more_coverage() -> None:
    """Cover remaining lines"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c._request = mock.Mock()  # type: ignore[method-assign]

        # set_session invalid encryption
        with pytest.raises(ValueError, match="Invalid encryption value"):
            c.set_session(encryption="invalid")  # type: ignore

        # start_torrent bypass_queue
        c.start_torrent(ids=1, bypass_queue=True)
        assert c._request.call_args[0][0] == "torrent-start-now"

        # get_torrents with arguments
        c._request.return_value = {"torrents": []}
        c.get_torrents(ids=1, arguments=["name"])
        args = c._request.call_args[0][1]["fields"]
        assert "name" in args
        assert "id" in args

        # get_recently_active_torrents with arguments
        c._request.return_value = {"torrents": [], "removed": []}
        c.get_recently_active_torrents(arguments=["name"])
        args = c._request.call_args[0][1]["fields"]
        assert "name" in args

        # free_space success
        c._request.return_value = {"path": "/tmp", "size-bytes": 100}
        assert c.free_space("/tmp") == 100

        # free_space fail
        c._request.return_value = {"path": "/other", "size-bytes": 0}
        assert c.free_space("/tmp") is None


def test_add_torrent_types() -> None:
    """Cover add_torrent with different input types"""

    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c._request = mock.Mock(return_value={"torrent-added": {"id": 1, "name": "n", "hashString": "h"}})  # type: ignore[method-assign]

        # bytes
        c.add_torrent(b"torrent content")
        assert "metainfo" in c._request.call_args[0][1]

        # file-like
        f = io.BytesIO(b"torrent content")
        c.add_torrent(f)
        assert "metainfo" in c._request.call_args[0][1]

        # Path (local file)
        # We need to mock path reading
        p = pathlib.Path("test.torrent")
        with mock.patch("pathlib.Path.read_bytes", return_value=b"content"):
            c.add_torrent(p)
        assert "metainfo" in c._request.call_args[0][1]


def test_final_straw() -> None:
    """Cover the last few lines"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c._request = mock.Mock()  # type: ignore[method-assign]

        # 489: empty metadata
        with pytest.raises(ValueError, match="Torrent metadata is empty"):
            c.add_torrent(b"")

        # 1255: _try_read_torrent returns None for unknown type
        # We pass an object that is not str/Path/bytes/read
        obj = object()
        # It returns None, so code proceeds to: kwargs["filename"] = obj
        # Then calls _request.
        c._request.return_value = {"torrent-added": {"id": 1}}
        c.add_torrent(obj)  # type: ignore

        # start_all bypass_queue with torrents to fully exercise logic
        c._request.side_effect = [
            {"torrents": [{"id": 1, "hashString": "h", "queuePosition": 0}]},  # get_torrents
            {},  # start
        ]
        c.start_all(bypass_queue=True)
        # Check second call argument
        assert c._request.call_args_list[-1][0][0] == "torrent-start-now"

    # Use a new client to test _request logic because we need the real _request to run
    # Client.get_session is already patched by the outer context if we are not careful
    # But here we are outside the with block of c

    with mock.patch.object(Client, "get_session", autospec=True):
        c2 = Client()
        c2.logger = mock.Mock()

        # 1. SessionStats fallback (358)
        c2._http_query = mock.Mock(  # type: ignore[method-assign]
            return_value=json.dumps({"result": "success", "arguments": {"activeTorrentCount": 1}})
        )
        stats = c2.session_stats()
        assert stats.active_torrent_count == 1

        # 2. TorrentAdd logic (338)
        c2._http_query.return_value = json.dumps(
            {"result": "success", "arguments": {"torrent-added": {"id": 1, "name": "n", "hashString": "h"}}}
        )
        # add_torrent calls _request. We pass 'magnet' so it doesn't try to read file.
        t = c2.add_torrent("magnet:?xt=urn:btih:h")
        assert t.id == 1

        # 3. get_torrent finding torrent (593-594)
        c2._http_query.return_value = json.dumps(
            {"result": "success", "arguments": {"torrents": [{"id": 1, "name": "n", "hashString": "h"}]}}
        )
        t = c2.get_torrent(1)
        assert t.id == 1


def test_add_torrent_duplicate(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined]
        status=200,
        headers={},
        data=json.dumps(
            {"result": "success", "arguments": {"torrent-duplicate": {"id": 1, "name": "test", "hashString": "hash"}}}
        ).encode(),
    )
    res = client.add_torrent("magnet:?xt=urn:btih:hash")
    assert res.id == 1


def test_add_torrent_invalid_response(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined]
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    with pytest.raises(TransmissionError, match="Invalid torrent-add response"):
        client.add_torrent("magnet:?xt=urn:btih:hash")


def test_get_torrent_not_found(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined]
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {"torrents": []}}).encode()
    )
    with pytest.raises(KeyError, match="Torrent not found"):
        client.get_torrent(1)


def test_session_stats_legacy(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined]
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
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined]
        status=200,
        headers={},
        data=json.dumps({"result": "success", "arguments": {"path": "/other", "size-bytes": 100}}).encode(),
    )
    assert client.free_space("/test") is None


def test_get_group_none(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined]
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {"group": []}}).encode()
    )
    assert client.get_group("test") is None


def test_client_void_methods(client: Client) -> None:
    # Set default success response
    client._Client__http_client.request.return_value.data = json.dumps(  # type: ignore[attr-defined]
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
        ("move_torrent_data", {"ids": 1, "location": "/tmp"}),
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
    client._Client__http_client.request.return_value.data = json.dumps(  # type: ignore[attr-defined]
        {
            "result": "success",
            "arguments": {},
        }
    ).encode()
    client.change_torrent(ids=1, download_limit=100)


def test_rename_torrent_path(client: Client) -> None:
    client._Client__http_client.request.return_value.data = json.dumps(  # type: ignore[attr-defined]
        {
            "result": "success",
            "arguments": {"path": "/a", "name": "b"},
        }
    ).encode()
    client.rename_torrent_path(1, "/path", "name")


def test_blocklist_update_extended(client: Client) -> None:
    client._Client__http_client.request.return_value.data = json.dumps(  # type: ignore[attr-defined]
        {
            "result": "success",
            "arguments": {"blocklist-size": 10},
        }
    ).encode()
    assert client.blocklist_update() == 10


def test_port_test(client: Client) -> None:
    client._Client__http_client.request.return_value.data = json.dumps(  # type: ignore[attr-defined]
        {
            "result": "success",
            "arguments": {"port-is-open": True, "ip_protocol": "ipv4"},
        }
    ).encode()
    assert client.port_test().port_is_open is True


def test_get_recently_active_torrents_extended(client: Client) -> None:
    client._Client__http_client.request.return_value.data = json.dumps(  # type: ignore[attr-defined]
        {
            "result": "success",
            "arguments": {"torrents": [], "removed": []},
        }
    ).encode()
    client.get_recently_active_torrents()


def test_get_groups_extended(client: Client) -> None:
    client._Client__http_client.request.return_value.data = json.dumps(  # type: ignore[attr-defined]
        {
            "result": "success",
            "arguments": {"group": []},
        }
    ).encode()
    client.get_groups()


def test_start_all_extended(client: Client) -> None:
    client._Client__http_client.request.reset_mock()  # type: ignore[attr-defined]
    # start_all calls get_torrents first to sort by queue position
    client._Client__http_client.request.side_effect = [  # type: ignore[attr-defined]
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
    assert client._Client__http_client.request.call_count == 2  # type: ignore[attr-defined]


def test_rpc_version_warning(client: Client) -> None:
    # Set low protocol version
    client._Client__protocol_version = 1  # type: ignore[attr-defined]
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client._rpc_version_warning(2)
        mock_warn.assert_called()


def test_set_session_warnings_extended(client: Client) -> None:
    client._Client__protocol_version = 16  # type: ignore[attr-defined]
    client._Client__http_client.request.return_value.data = json.dumps({"result": "success", "arguments": {}}).encode()  # type: ignore[attr-defined]
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.set_session(default_trackers=["a"])
        mock_warn.assert_called()


def test_change_torrent_warnings_extended(client: Client) -> None:
    client._Client__protocol_version = 15  # type: ignore[attr-defined]
    client._Client__http_client.request.return_value.data = json.dumps({"result": "success", "arguments": {}}).encode()  # type: ignore[attr-defined]
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.change_torrent(ids=1, labels=["a"])
        mock_warn.assert_called()


def test_parsing_ids(client: Client) -> None:
    # 75: invalid hex string length
    with pytest.raises(ValueError, match="not valid torrent id"):
        client.get_torrent("a")  # length != 40

    # 75: invalid hex string content
    with pytest.raises(ValueError, match="not valid torrent id"):
        client.get_torrent("z" * 40)

    # 77: invalid type for _parse_torrent_id (called via get_torrent -> _parse_torrent_ids -> _parse_torrent_id)
    # Wait, _parse_torrent_ids handles int, str, list.
    # If list has invalid type?
    with pytest.raises(ValueError, match="is not valid torrent id"):
        client.start_torrent(ids=[object()])  # type: ignore

    # 90: valid hash string
    h = "a" * 40
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined]
        status=200,
        headers={},
        data=json.dumps({"result": "success", "arguments": {"torrents": []}}).encode(),
    )
    with contextlib.suppress(KeyError):
        client.get_torrent(h)

    # 93: invalid type for _parse_torrent_ids (e.g. float)
    with pytest.raises(ValueError, match="Invalid torrent id"):
        client.start_torrent(ids=1.5)  # type: ignore
