from __future__ import annotations

import base64
import datetime
import pathlib

import pytest

from transmission_rpc import utils
from transmission_rpc.client import (
    _single_str_as_list,
    _try_read_torrent,
    ensure_location_str,
    list_or_none,
    remove_unset_value,
)


@pytest.mark.parametrize(
    ("delta", "expected"),
    list(
        {
            datetime.timedelta(0, 0): "0 00:00:00",
            datetime.timedelta(0, 10): "0 00:00:10",
            datetime.timedelta(0, 60): "0 00:01:00",
            datetime.timedelta(0, 61): "0 00:01:01",
            datetime.timedelta(0, 3661): "0 01:01:01",
            datetime.timedelta(1, 3661): "1 01:01:01",
            datetime.timedelta(13, 65660): "13 18:14:20",
        }.items()
    ),
)
def test_format_timedelta(delta: datetime.timedelta, expected: str) -> None:
    """
    Verify that `format_timedelta` formats timedelta objects into strings as expected.
    """
    assert utils.format_timedelta(delta) == expected, f"format_timedelta({delta}) != {expected}"


def test_remove_unset_value() -> None:
    """
    Verify that `remove_unset_value` removes keys with `None` values from a dictionary.
    """
    assert remove_unset_value({"a": 1, "b": None}) == {"a": 1}


def test_single_str_as_list() -> None:
    """
    Verify `_single_str_as_list` converts a single string to a list of that string,
    keeps lists as is, and returns None for None.
    """
    assert _single_str_as_list(None) is None
    assert _single_str_as_list("a") == ["a"]
    assert _single_str_as_list(["a"]) == ["a"]


def test_ensure_location_str() -> None:
    """Verify that ensure_location_str handles Path objects and strings correctly."""
    p = pathlib.Path.cwd() / "tmp"
    assert ensure_location_str(p) == str(p)
    assert ensure_location_str("/already/string") == "/already/string"


def test_ensure_location_str_error() -> None:
    """
    Verify that `ensure_location_str` raises ValueError if the path is relative.
    Cover ensure_location_str relative path error
    """
    p = pathlib.Path("relative/path")
    with pytest.raises(ValueError, match=r"using relative `pathlib.Path`"):
        ensure_location_str(p)


def test_list_or_none() -> None:
    """
    Verify `list_or_none` converts iterables to lists and returns None for None.
    """
    assert list_or_none(None) is None
    assert list_or_none([1]) == [1]
    assert list_or_none((1,)) == [1]


def test_try_read_torrent_file_url() -> None:
    """
    Verify that `_try_read_torrent` raises ValueError when encountering a `file://` URL,
    as support for it has been removed.
    """
    with pytest.raises(ValueError, match="support for `file://` URL has been removed"):
        _try_read_torrent("file:///tmp/a.torrent")


torrent_hash = "e84213a794f3ccd890382a54a64ca68b7e925433"
magnet_url = f"magnet:?xt=urn:btih:{torrent_hash}"
torrent_url = "https://github.com/trim21/transmission-rpc/raw/v4.1.0/tests/fixtures/iso.torrent"


def test_try_read_torrent_http_url() -> None:
    """
    Verify that `_try_read_torrent` returns None for a standard HTTP URL,
    indicating it should be handled by the daemon directly.
    """
    assert _try_read_torrent(torrent_url) is None, "Should return None for HTTP URLs (let daemon handle it)"


def test_try_read_torrent_magnet() -> None:
    """
    Verify that `_try_read_torrent` returns None for a magnet link,
    indicating it should be handled by the daemon directly.
    """
    assert _try_read_torrent(magnet_url) is None, "Should return None for magnet URLs (let daemon handle it)"


def test_try_read_torrent_pathlib_path() -> None:
    """
    Verify that `_try_read_torrent` correctly reads and base64 encodes the content of a local file provided as a Path object.
    """
    p = pathlib.Path("tests/fixtures/iso.torrent")
    b64 = base64.b64encode(p.read_bytes()).decode()
    assert _try_read_torrent(p) == b64, "Should correctly read and base64 encode content from a Path object"


def test_try_read_torrent_file_object() -> None:
    """
    Verify that `_try_read_torrent` correctly reads and base64 encodes the content of an open file object.
    """
    with open("tests/fixtures/iso.torrent", "rb") as f:
        content = f.read()
        f.seek(0)
        data = _try_read_torrent(f)

    assert base64.b64encode(content).decode() == data, "Should correctly base64 encode content from a file object"


def test_try_read_torrent_bytes() -> None:
    """
    Verify that `_try_read_torrent` correctly base64 encodes raw bytes content.
    """
    with open("tests/fixtures/iso.torrent", "rb") as f:
        content = f.read()
    data = _try_read_torrent(content)
    assert base64.b64encode(content).decode() == data, "Should correctly base64 encode raw bytes"
