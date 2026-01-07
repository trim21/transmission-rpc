import contextlib
from typing import Any

from transmission_rpc.session import Session, SessionStats, Stats, Units


def check_properties(cls: type, obj: Any) -> None:
    for prop in dir(cls):
        if isinstance(getattr(cls, prop), property):
            with contextlib.suppress(KeyError, DeprecationWarning):
                getattr(obj, prop)


def test_session_property_explicit() -> None:
    # Coverage for session.py line 370
    s = Session(fields={"script-torrent-done-seeding-enabled": True})
    val = s.script_torrent_done_seeding_enabled
    assert val is True


def test_session_default_trackers() -> None:
    """Cover session default_trackers property"""
    s = Session(fields={"default-trackers": "t1\nt2"})
    assert s.default_trackers == ["t1", "t2"]

    s2 = Session(fields={})
    assert s2.default_trackers is None


def test_session_default_trackers_branches() -> None:
    """
    Test branches in default_trackers property.
    Existing tests only cover the None case.
    """
    # Case 1: default-trackers is a newline-separated string
    s1 = Session(fields={"default-trackers": "http://t1.com\nhttp://t2.com"})
    assert s1.default_trackers == ["http://t1.com", "http://t2.com"]

    # Case 2: default-trackers is already a list
    s2 = Session(fields={"default-trackers": ["http://t3.com"]})
    assert s2.default_trackers == ["http://t3.com"]


def test_script_torrent_added_filename() -> None:
    """
    Explicitly test script_torrent_added_filename to ensure coverage
    at the reported line 372.
    """
    s = Session(fields={"script-torrent-added-filename": "my_script.sh"})
    assert s.script_torrent_added_filename == "my_script.sh"


def test_session_properties_access() -> None:
    s = Session(fields={})
    check_properties(Session, s)


def test_session_stats_properties_access() -> None:
    s = SessionStats(fields={})
    check_properties(SessionStats, s)


def test_stats_properties_access() -> None:
    s = Stats(fields={})
    check_properties(Stats, s)


def test_units_properties_access() -> None:
    u = Units(fields={})
    check_properties(Units, u)


def test_session_missing_properties() -> None:
    s = Session(fields={"script-torrent-done-seeding-enabled": True})
    assert s.script_torrent_done_seeding_enabled is True
