"""Protocol-level tests: JSON-RPC 2.0 requests/responses, legacy fallback,
and field-name conversion at the protocol boundary."""

import json
from typing import Any
from unittest import mock

import pytest

from transmission_rpc._compat import convert_jsonrpc_args, convert_request_args, legacy_name, to_snake
from transmission_rpc.client import Client
from transmission_rpc.error import TransmissionError
from transmission_rpc.session import Session
from transmission_rpc.torrent import Torrent


def test_new_protocol_request_format(mock_network: Any, success_response: Any) -> None:
    """Verify requests use the JSON-RPC 2.0 envelope with snake_case method."""
    mock_network.return_value = success_response()
    c = Client()

    c.start_torrent(ids=[1])

    sent = mock_network.call_args_list[-1][1]["json"]
    assert sent["jsonrpc"] == "2.0"
    assert sent["method"] == "torrent_start"
    assert sent["params"] == {"ids": [1]}
    assert isinstance(sent["id"], int)


def test_request_id_increments(mock_network: Any, success_response: Any) -> None:
    """Verify the request id increments per request."""
    mock_network.return_value = success_response()
    c = Client()

    c.get_session()
    c.start_torrent(ids=1)

    ids = [call[1]["json"]["id"] for call in mock_network.call_args_list]
    assert ids == sorted(ids)
    assert len(set(ids)) == len(ids)


def test_probe_falls_back_to_legacy(mock_network: Any, legacy_response: Any) -> None:
    """Verify the first request probes JSON-RPC 2.0 and falls back to the
    legacy protocol when the server answers without the `jsonrpc` field."""
    mock_network.side_effect = [
        legacy_response(),  # probe answer (legacy format)
        legacy_response(),  # legacy resend of the initial session_get
    ]
    c = Client()

    # The probe request used the JSON-RPC envelope...
    assert mock_network.call_args_list[0][1]["json"]["jsonrpc"] == "2.0"
    # ...the resend used the legacy envelope with kebab-case method.
    resend = mock_network.call_args_list[1][1]["json"]
    assert "jsonrpc" not in resend
    assert resend["method"] == "session-get"
    assert "rpc-version" in resend["arguments"]["fields"]
    assert c._Client__use_jsonrpc is False  # noqa: SLF001


def test_legacy_probe_retry_rejects_invalid_json(mock_network: Any, legacy_response: Any) -> None:
    mock_network.side_effect = [
        legacy_response(),
        mock.Mock(status=200, headers={}, data=b"invalid json"),
    ]

    with pytest.raises(TransmissionError, match="failed to parse response"):
        Client()


def test_legacy_response_errors(mock_network: Any, legacy_response: Any) -> None:
    mock_network.side_effect = [legacy_response(), legacy_response()]
    client = Client()

    mock_network.side_effect = None
    mock_network.return_value = mock.Mock(
        status=200,
        headers={},
        data=json.dumps({"arguments": {}}).encode(),
    )
    with pytest.raises(TransmissionError, match="missing without result"):
        client.get_session()

    mock_network.return_value = mock.Mock(
        status=200,
        headers={},
        data=json.dumps({"result": "legacy failure", "arguments": {}}).encode(),
    )
    with pytest.raises(TransmissionError, match="legacy failure"):
        client.get_session()


def test_rpc_version_warnings_for_new_fields(mock_network: Any, legacy_response: Any) -> None:
    mock_network.side_effect = [legacy_response(), legacy_response(), legacy_response(), legacy_response()]
    client = Client()

    with mock.patch.object(client.logger, "warning") as warning:
        client.change_torrent(1, sequential_download_from_piece=3)
        client.set_session(preferred_transports=["tcp"])

    assert warning.call_count == 2


def test_authenticated_request_redacts_debug_headers(mock_network: Any, success_response: Any) -> None:
    mock_network.return_value = success_response()

    client = Client(username="user", password="password")  # noqa: S106

    assert client.get_session().rpc_version == 18


def test_legacy_requests_convert_args_by_method(mock_network: Any, legacy_response: Any) -> None:
    """Verify snake_case request args are converted to the correct legacy
    variant depending on the method context."""
    mock_network.side_effect = [
        legacy_response(),
        legacy_response(),
        legacy_response(),
        legacy_response(),
    ]
    c = Client()

    c.change_torrent(ids=1, download_dir="/d", bandwidth_priority=1, seed_ratio_limit=2.0)
    torrent_set = mock_network.call_args_list[-1][1]["json"]["arguments"]
    assert torrent_set == {"ids": [1], "downloadDir": "/d", "bandwidthPriority": 1, "seedRatioLimit": 2.0}

    c.set_session(download_dir="/s", alt_speed_down=100)
    session_set = mock_network.call_args_list[-1][1]["json"]["arguments"]
    assert session_set == {"download-dir": "/s", "alt-speed-down": 100}


def test_legacy_fields_and_ids_conversion(mock_network: Any, legacy_response: Any) -> None:
    """Verify torrent-get `fields` values and the `recently_active` ids value
    are converted to their legacy spellings."""
    mock_network.side_effect = [
        legacy_response(),  # init probe
        legacy_response(),  # init legacy resend
        legacy_response({"torrents": [], "removed": []}),  # get_torrents
        legacy_response({"torrents": [], "removed": []}),  # get_recently_active_torrents
    ]
    c = Client()

    c.get_torrents(arguments=["name", "hash_string"])
    sent = mock_network.call_args_list[-1][1]["json"]["arguments"]
    assert "hashString" in sent["fields"]

    c.get_recently_active_torrents()
    sent = mock_network.call_args_list[-1][1]["json"]["arguments"]
    assert sent["ids"] == "recently-active"


def test_legacy_response_fields_use_getter_fallback(mock_network: Any, legacy_response: Any) -> None:
    """Legacy response dictionaries stay raw while getters accept old names."""
    mock_network.side_effect = [
        legacy_response(),  # init probe
        legacy_response(),  # init legacy resend
        legacy_response(
            {
                "torrents": [
                    {
                        "id": 1,
                        "hashString": "hash1",
                        "downloadDir": "/d",
                        "file-count": 2,
                        "seedRatioLimit": 2.0,
                        "fileStats": [{"bytesCompleted": 8, "wanted": True, "priority": 0}],
                        "peers": [{"address": "127.0.0.1", "isUTP": True}],
                    }
                ]
            }
        ),
    ]
    c = Client()

    t = c.get_torrent(1)
    assert "hashString" in t.fields
    assert "hash_string" not in t.fields
    assert t.hash_string == "hash1"
    assert t.download_dir == "/d"
    assert t.file_count == 2
    assert t.seed_ratio_limit == 2.0
    assert t.file_stats[0].bytes_completed == 8
    assert t.peers[0].is_utp is True

    session = Session(fields={"cache-size-mb": 8})
    assert session.cache_size_mib == 8
    assert not hasattr(Session, "cache_size_mb")
    assert not hasattr(Session, "download_dir_free_space")


def test_jsonrpc_error_response(success_response: Any) -> None:
    """Verify a JSON-RPC error object raises TransmissionError with the message
    and any `error_string` detail."""
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        mock_req.side_effect = [
            success_response(),
            mock.Mock(
                status=200,
                headers={},
                data=json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "error": {"code": 3, "message": "path is not absolute", "data": {"error_string": "detail"}},
                        "id": 2,
                    }
                ).encode(),
            ),
        ]
        c = Client()
        with pytest.raises(TransmissionError, match="path is not absolute: detail"):
            c.free_space("/relative")


def test_container_get_accepts_legacy_keys() -> None:
    """Verify Container.get accepts both snake_case and legacy keys."""
    t = Torrent(fields={"id": 1, "hash_string": "h", "download_dir": "/d"})
    assert t.get("hash_string") == "h"
    assert t.get("hashString") == "h"
    assert t.get("download_dir") == "/d"
    assert t.get("download-dir") == "/d"
    assert t.get("downloadDir") == "/d"
    assert t.get("missing") is None


def test_compat_rule_conversion() -> None:
    """Verify the field-name conversion rules and known exceptions."""
    assert to_snake("clientName") == "client_name"
    assert to_snake("isUTP") == "is_utp"
    assert to_snake("alt-speed-down") == "alt_speed_down"
    assert to_snake("cache-size-mb") == "cache_size_mib"

    assert legacy_name("alt_speed_down", torrent=False) == "alt-speed-down"
    assert legacy_name("bandwidth_priority", torrent=False) == "bandwidthPriority"
    assert legacy_name("bandwidth_priority", torrent=True) == "bandwidthPriority"
    assert legacy_name("download_dir", torrent=False) == "download-dir"
    assert legacy_name("download_dir", torrent=True) == "downloadDir"
    # 4.0.x uses the camelCase variant in every RPC method for these
    assert legacy_name("seed_ratio_limit", torrent=False) == "seedRatioLimit"
    assert legacy_name("seed_ratio_limit", torrent=True) == "seedRatioLimit"
    assert legacy_name("unknown_field", torrent=False) == "unknown_field"


def test_request_value_compatibility() -> None:
    assert convert_jsonrpc_args({"encryption": "tolerated"}) == {"encryption": "allowed"}
    assert convert_jsonrpc_args({"fields": ["hashString"], "ids": "recently-active"}) == {
        "fields": ["hash_string"],
        "ids": "recently_active",
    }
    assert convert_request_args({"encryption": "allowed"}, torrent=False) == {"encryption": "tolerated"}
    assert convert_request_args({"download_dir": "/d"}, torrent=False) == {"download-dir": "/d"}
    assert convert_request_args({"download_dir": "/d"}, torrent=True) == {"downloadDir": "/d"}


def test_encryption_value_is_converted_for_selected_protocol(
    mock_network: Any, success_response: Any, legacy_response: Any
) -> None:
    mock_network.side_effect = [success_response(), success_response()]
    client = Client()
    client.set_session(encryption="tolerated")
    assert mock_network.call_args.kwargs["json"]["params"]["encryption"] == "allowed"

    mock_network.reset_mock()
    mock_network.side_effect = [legacy_response(), legacy_response(), legacy_response()]
    client = Client()
    client.set_session(encryption="allowed")
    assert mock_network.call_args.kwargs["json"]["arguments"]["encryption"] == "tolerated"


def test_legacy_torrent_add_uses_kebab_download_dir(mock_network: Any, legacy_response: Any) -> None:
    mock_network.side_effect = [
        legacy_response(),
        legacy_response(),
        legacy_response({"torrent-added": {"id": 1, "name": "test", "hashString": "hash"}}),
    ]
    client = Client()

    torrent = client.add_torrent("magnet:?xt=urn:btih:hash", download_dir="/downloads")

    assert mock_network.call_args.kwargs["json"]["arguments"]["download-dir"] == "/downloads"
    assert torrent.fields["hashString"] == "hash"
    assert torrent.hash_string == "hash"
