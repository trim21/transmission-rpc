import base64
import io
import pathlib
from typing import Any, cast
from unittest import mock

import pytest

from transmission_rpc.client import Client
from transmission_rpc.error import TransmissionError


def test_set_session_excludes_none_values(mock_network: Any, success_response: Any) -> None:
    """
    Verify that None values in kwargs are removed from the payload sent to the server.

    Verify `remove_unset_value` logic via `Client.set_session`.
    Passing `None` for a keyword argument should exclude it from the RPC payload.
    """
    mock_network.return_value = success_response()
    c = Client()

    # We pass explicit None for 'speed_limit_down_enabled'
    c.set_session(speed_limit_down_enabled=None, speed_limit_up_enabled=True)

    sent_args = mock_network.call_args[1]["json"]["arguments"]
    assert "speed-limit-up-enabled" in sent_args
    # "speed-limit-down-enabled" should be removed because it was None
    assert "speed-limit-down-enabled" not in sent_args


def test_move_torrent_converts_path_to_str(mock_network: Any, tmp_path: pathlib.Path, success_response: Any) -> None:
    """
    Verify `ensure_location_str` logic via `Client.move_torrent_data`.
    """
    mock_network.return_value = success_response()
    c = Client()

    # Test Path object - Force absolute to pass validation on all OSs
    p = (tmp_path / "path").absolute()
    c.move_torrent_data(ids=1, location=p)
    sent_args = mock_network.call_args[1]["json"]["arguments"]
    assert sent_args["location"] == str(p)

    # Test String
    c.move_torrent_data(ids=1, location="/str/path")
    sent_args = mock_network.call_args[1]["json"]["arguments"]
    assert sent_args["location"] == "/str/path"


def test_move_torrent_raises_on_relative_path(mock_network: Any, success_response: Any) -> None:
    """
    Verify `ensure_location_str` raises ValueError for relative paths via `Client.move_torrent_data`.
    """
    mock_network.return_value = success_response()
    c = Client()
    # Force relative path
    p = pathlib.Path("relative/path")
    with pytest.raises(ValueError, match="using relative"):
        c.move_torrent_data(ids=1, location=p)


def test_add_torrent_serializes_list_arguments(mock_network: Any, success_response: Any) -> None:
    """
    Verify `list_or_none` logic via `Client.add_torrent`.
    Arguments like 'files_wanted' are processed by list_or_none.
    """
    mock_network.return_value = success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}})
    c = Client()

    # 1. Single int -> [int]
    c.add_torrent("magnet:?", files_wanted=[1])
    args = mock_network.call_args[1]["json"]["arguments"]
    assert args["files-wanted"] == [1]

    # 2. List -> List
    c.add_torrent("magnet:?", files_wanted=[2])
    args = mock_network.call_args[1]["json"]["arguments"]
    assert args["files-wanted"] == [2]

    # 3. None -> Not in arguments (handled by logic)
    c.add_torrent("magnet:?", files_wanted=None)
    args = mock_network.call_args[1]["json"]["arguments"]
    assert "files-wanted" not in args


def test_add_torrent_sends_url_as_filename_argument(mock_network: Any, success_response: Any) -> None:
    """
    Verify `_try_read_torrent` logic via `Client.add_torrent` for URLs.
    """
    mock_network.return_value = success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}})
    c = Client()

    # HTTP URL -> Passed as filename (internal logic returns None, so client sends as filename)
    url = "http://example.com/file.torrent"
    c.add_torrent(url)
    args = mock_network.call_args[1]["json"]["arguments"]
    assert args["filename"] == url
    assert "metainfo" not in args

    # Magnet URL -> Passed as filename
    magnet = "magnet:?xt=urn:btih:abc"
    c.add_torrent(magnet)
    args = mock_network.call_args[1]["json"]["arguments"]
    assert args["filename"] == magnet
    assert "metainfo" not in args


def test_add_torrent_raises_on_file_scheme(mock_network: Any, success_response: Any) -> None:
    """Verify that using the `file://` scheme in `add_torrent` raises a ValueError."""
    mock_network.return_value = success_response()
    c = Client()
    with pytest.raises(ValueError, match="support for `file://` URL has been removed"):
        c.add_torrent("file:///tmp/test.torrent")


def test_add_torrent_args(mock_network: Any, success_response: Any) -> None:
    """Verify that `add_torrent` correctly serializes optional arguments (e.g., `labels`, `bandwidthPriority`) into the RPC payload."""
    mock_network.side_effect = [
        success_response(),  # init
        success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}}),
    ]

    c = Client()
    c.add_torrent("magnet:?xt=urn:btih:a", labels=["l"], sequential_download=True, bandwidthPriority=1)

    sent_args = mock_network.call_args[1]["json"]["arguments"]
    assert sent_args["labels"] == ["l"]
    assert sent_args["sequential_download"] is True
    assert sent_args["bandwidthPriority"] == 1


def test_add_torrent_handles_various_input_types(mock_network: Any, success_response: Any) -> None:
    """Cover `add_torrent` with different input types."""
    mock_network.side_effect = [
        success_response(),  # init
        success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}}),
        success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}}),
        success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}}),
    ]
    c = Client()

    # bytes
    content = b"torrent content"
    encoded = base64.b64encode(content).decode()
    c.add_torrent(content)
    assert mock_network.call_args[1]["json"]["arguments"]["metainfo"] == encoded

    # file-like
    f = io.BytesIO(b"torrent content")
    c.add_torrent(f)
    assert "metainfo" in mock_network.call_args[1]["json"]["arguments"]

    # Path (local file)
    p = pathlib.Path("test.torrent")
    with mock.patch("pathlib.Path.read_bytes", return_value=b"content"):
        c.add_torrent(p)
    assert "metainfo" in mock_network.call_args[1]["json"]["arguments"]


def test_add_torrent_raises_on_invalid_metadata(mock_network: Any, success_response: Any) -> None:
    """Verify `add_torrent` raises ValueError for empty metadata or unknown input types."""
    mock_network.return_value = success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}})
    c = Client()

    # Empty bytes
    with pytest.raises(ValueError, match="Torrent metadata is empty"):
        c.add_torrent(b"")

    # Pass an unknown type to verify fallback logic
    obj = object()
    c.add_torrent(cast("Any", obj))
    # Should treat as filename
    assert mock_network.call_args[1]["json"]["arguments"]["filename"] is obj


def test_add_torrent_duplicate(mock_network: Any, success_response: Any) -> None:
    """Verify that `add_torrent` handles the 'torrent-duplicate' response correctly."""
    mock_network.side_effect = [
        success_response(),
        success_response({"torrent-duplicate": {"id": 1, "name": "test", "hashString": "hash"}}),
    ]
    c = Client()
    res = c.add_torrent("magnet:?xt=urn:btih:hash")
    assert res.id == 1


def test_add_torrent_invalid_response(mock_network: Any, success_response: Any) -> None:
    """Verify that `add_torrent` raises TransmissionError if response is invalid (empty/malformed)."""
    mock_network.side_effect = [success_response(), success_response({})]
    c = Client()
    with pytest.raises(TransmissionError, match="Invalid torrent-add response"):
        c.add_torrent("magnet:?xt=urn:btih:hash")


def test_add_torrent_unexpected_data(mock_network: Any, success_response: Any) -> None:
    """Verify add_torrent raises TransmissionError if response contains unexpected data."""
    mock_network.side_effect = [
        success_response(),
        success_response({"unexpected": "data"}),
    ]
    c = Client()
    with pytest.raises(TransmissionError, match="Invalid torrent-add response"):
        c.add_torrent("magnet:?")


def test_add_torrent_labels_single_string(mock_network: Any, success_response: Any) -> None:
    """Verify add_torrent handles a single string for labels."""
    mock_network.return_value = success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}})
    c = Client()
    c.add_torrent("magnet:?", labels="one_label")

    args = mock_network.call_args[1]["json"]["arguments"]
    assert args["labels"] == ["one_label"]


def test_add_torrent_treats_string_as_filename(
    mock_network: Any, tmp_path: pathlib.Path, success_response: Any
) -> None:
    """Verify add_torrent with a filename string (not URL)."""
    mock_network.return_value = success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}})
    c = Client()
    # Pass a string that looks like a filename, not a URL
    filename = str(tmp_path / "test.torrent")
    c.add_torrent(filename)

    args = mock_network.call_args[1]["json"]["arguments"]
    # It should be treated as a filename, not metainfo
    assert args["filename"] == filename
    assert "metainfo" not in args
