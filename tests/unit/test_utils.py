import pathlib

import pytest

from tests.util import ServerTooLowError, skip_on
from transmission_rpc.client import (
    _single_str_as_list,
    _try_read_torrent,
    ensure_location_str,
    list_or_none,
    remove_unset_value,
)


def test_remove_unset_value() -> None:
    assert remove_unset_value({"a": 1, "b": None}) == {"a": 1}


def test_single_str_as_list() -> None:
    assert _single_str_as_list(None) is None
    assert _single_str_as_list("a") == ["a"]
    assert _single_str_as_list(["a"]) == ["a"]


def test_ensure_location_str() -> None:
    # Only test the Path branch as str is trivial
    p = pathlib.Path.cwd() / "tmp"
    assert ensure_location_str(p) == str(p)


def test_ensure_location_str_error() -> None:
    """Cover ensure_location_str relative path error"""
    p = pathlib.Path("relative/path")
    with pytest.raises(ValueError, match=r"using relative `pathlib.Path`"):
        ensure_location_str(p)


def test_util_skip_on() -> None:
    @skip_on(ServerTooLowError, "reason")  # type: ignore[no-untyped-call, untyped-decorator]
    def func() -> None:
        raise ServerTooLowError

    # Calling func should skip
    func()


def test_list_or_none() -> None:
    assert list_or_none(None) is None
    assert list_or_none([1]) == [1]
    assert list_or_none((1,)) == [1]


def test_try_read_torrent_file_url() -> None:
    with pytest.raises(ValueError, match="support for `file://` URL has been removed"):
        _try_read_torrent("file:///tmp/a.torrent")
