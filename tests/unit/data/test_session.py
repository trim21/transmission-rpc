from tests.util import check_properties
from transmission_rpc.session import Session, SessionStats, Stats, Units


def test_session_property_explicit() -> None:
    """
    Verify that explicit session properties (like `script_torrent_done_seeding_enabled`)
    are correctly populated from the initialization fields.
    """
    s = Session(fields={"script_torrent_done_seeding_enabled": True})
    val = s.script_torrent_done_seeding_enabled
    assert val is True


def test_session_default_trackers_list_input() -> None:
    """
    Verify `default_trackers` handles different input formats:
    - Newline-separated string.
    - Pre-existing list.
    - Missing fields (None).
    """
    # Case 1: default-trackers is a newline-separated string
    s1 = Session(fields={"default_trackers": "http://t1.com\nhttp://t2.com"})
    assert s1.default_trackers == ["http://t1.com", "http://t2.com"]

    # Case 2: default-trackers is already a list
    s2 = Session(fields={"default_trackers": ["http://t3.com"]})
    assert s2.default_trackers == ["http://t3.com"]

    # Case 3: default-trackers is missing
    s3 = Session(fields={})
    assert s3.default_trackers is None


def test_script_torrent_added_filename() -> None:
    """
    Verify that `script_torrent_added_filename` is correctly retrieved from fields.
    """
    s = Session(fields={"script_torrent_added_filename": "my_script.sh"})
    assert s.script_torrent_added_filename == "my_script.sh"


def test_session_properties_access() -> None:
    """
    Verify that all public properties of the Session class can be accessed without error.
    """
    s = Session(fields={})
    check_properties(Session, s)


def test_session_stats_properties_access() -> None:
    """
    Verify that all public properties of the SessionStats class can be accessed without error.
    """
    s = SessionStats(fields={})
    check_properties(SessionStats, s)


def test_stats_properties_access() -> None:
    """
    Verify that all public properties of the Stats class can be accessed without error.
    """
    s = Stats(fields={})
    check_properties(Stats, s)


def test_units_properties_access() -> None:
    """
    Verify that all public properties of the Units class can be accessed without error.
    """
    u = Units(fields={})
    check_properties(Units, u)


def test_session_missing_properties() -> None:
    """
    Verify that session properties are correctly accessed even when initialized with minimal fields.
    """
    s = Session(fields={"script_torrent_done_seeding_enabled": True})
    assert s.script_torrent_done_seeding_enabled is True


def test_jsonrpc_2_session_fields() -> None:
    session = Session(
        fields={
            "anti_brute_force_enabled": True,
            "encryption": "allowed",
            "preferred_transports": ["utp", "tcp"],
            "reqq": 128,
            "sequential_download": True,
            "session_id": "session-id",
        }
    )

    assert session.anti_brute_force_enabled is True
    assert session.encryption == "allowed"
    assert session.preferred_transports == ["utp", "tcp"]
    assert session.reqq == 128
    assert session.sequential_download is True
    assert session.session_id == "session-id"
