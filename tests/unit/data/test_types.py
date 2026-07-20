import pytest

from tests.util import check_properties
from transmission_rpc.constants import Args, Type, get_torrent_arguments
from transmission_rpc.error import TransmissionError
from transmission_rpc.torrent import Peer, PeersFrom, Tracker, TrackerStats
from transmission_rpc.types import BitMap, Container, Group, PortTestResult, _FieldDict, _to_snake


def test_container_repr() -> None:
    """Verify that `Container.__repr__` returns the expected string format."""
    c = Container(fields={"key": "value"})
    assert repr(c) == "<Container fields={'key': 'value'}>"


def test_peer_properties_access() -> None:
    """Verify that all properties of the `Peer` class can be accessed without error."""
    p = Peer(fields={})
    check_properties(Peer, p)


def test_peers_from_properties_access() -> None:
    """Verify that all properties of the `PeersFrom` class can be accessed without error."""
    p = PeersFrom(fields={})
    check_properties(PeersFrom, p)


def test_tracker_properties_access() -> None:
    """Verify that all properties of the `Tracker` class can be accessed without error."""
    t = Tracker(fields={})
    check_properties(Tracker, t)


def test_tracker_stats_properties_access() -> None:
    """Verify that all properties of the `TrackerStats` class can be accessed without error."""
    t = TrackerStats(fields={})
    check_properties(TrackerStats, t)


def test_group_properties() -> None:
    """
    Verify that the `Group` class correctly maps fields to properties.
    """
    fields = {
        "name": "g1",
        "honorsSessionLimits": True,
        "speed-limit-down-enabled": False,
        "speed-limit-down": 100,
        "speed-limit-up-enabled": False,
        "speed-limit-up": 100,
    }
    g = Group(fields=fields)
    assert g.name == "g1"
    assert g.honors_session_limits is True
    assert g.speed_limit_down_enabled is False
    assert g.speed_limit_down == 100
    assert g.speed_limit_up_enabled is False
    assert g.speed_limit_up == 100


def test_port_test_result_properties() -> None:
    """
    Verify that the `PortTestResult` class correctly maps fields to properties.
    """
    fields = {"port-is-open": True, "ip_protocol": "ipv4"}
    r = PortTestResult(fields=fields)
    assert r.port_is_open is True
    assert r.ip_protocol == "ipv4"


def test_bitmap() -> None:
    """
    Verify that `BitMap` correctly interprets bytes as a sequence of boolean flags.
    """
    # 1 byte: 10101010 -> 0xAA.
    # Index 0 is MSB.
    # 0xAA = 170.
    # 10101010
    # 0: True, 1: False, 2: True, 3: False...
    b = BitMap(b"\xaa")
    assert b.get(0) is True
    assert b.get(1) is False
    assert b.get(7) is False
    assert b.get(8) is False  # out of bounds


def test_args_repr_str() -> None:
    """
    Verify `Args.__repr__` and `Args.__str__` output formats.
    """
    arg = Args(Type.number, 1, description="desc")
    assert repr(arg) == "Args('number', 1, None, None, None, 'desc')"
    assert str(arg) == "Args<type=number, 1, description='desc')"


def test_get_torrent_arguments() -> None:
    """
    Verify that `get_torrent_arguments` returns the expected set of arguments for a given RPC version.
    """
    args = get_torrent_arguments(1)
    assert "id" in args
    assert "group" not in args  # added in 17


def test_error_str_with_original() -> None:
    """
    Verify that `TransmissionError` correctly formats its string representation when wrapping another exception.
    """

    class MockError(Exception):
        def __str__(self) -> str:
            return "original error"

    original = MockError()
    err = TransmissionError("message", original=original)
    assert str(err) == 'message Original exception: MockError, "original error"'


def test_deprecated_raw_response() -> None:
    """
    Verify that accessing the deprecated `rawResponse` attribute of `TransmissionError` emits a warning.
    """
    err = TransmissionError("message", raw_response="raw")
    with pytest.warns(DeprecationWarning, match="use .raw_response instead"):
        assert err.rawResponse == "raw"


# ---------------------------------------------------------------------------
# _to_snake and _FieldDict tests
# ---------------------------------------------------------------------------


def test_to_snake_camel_case() -> None:
    """Verify camelCase is correctly converted to snake_case."""
    assert _to_snake("hashString") == "hash_string"
    assert _to_snake("downloadDir") == "download_dir"
    assert _to_snake("trackerStats") == "tracker_stats"
    assert _to_snake("peersGettingFromUs") == "peers_getting_from_us"
    assert _to_snake("isUTP") == "is_utp"
    assert _to_snake("seedRatioLimit") == "seed_ratio_limit"
    assert _to_snake("bandwidthPriority") == "bandwidth_priority"
    assert _to_snake("webseedsSendingToUs") == "webseeds_sending_to_us"
    assert _to_snake("rateToClient") == "rate_to_client"


def test_to_snake_kebab_case() -> None:
    """Verify kebab-case is correctly converted to snake_case."""
    assert _to_snake("file-count") == "file_count"
    assert _to_snake("peer-limit") == "peer_limit"
    assert _to_snake("alt-speed-down") == "alt_speed_down"
    assert _to_snake("rpc-version-semver") == "rpc_version_semver"
    assert _to_snake("speed-limit-down-enabled") == "speed_limit_down_enabled"


def test_to_snake_already_snake() -> None:
    """Verify that already-snake_case strings are not changed."""
    assert _to_snake("sequential_download") == "sequential_download"
    assert _to_snake("hash_string") == "hash_string"
    assert _to_snake("id") == "id"
    assert _to_snake("name") == "name"


def test_field_dict_camel_fallback() -> None:
    """Verify _FieldDict falls back to snake_case lookup for camelCase keys."""
    d = _FieldDict({"hash_string": "abc", "download_dir": "/tmp", "file_count": 5})
    assert d["hashString"] == "abc"
    assert d["downloadDir"] == "/tmp"
    assert d["file-count"] == 5  # kebab → snake


def test_field_dict_direct_hit() -> None:
    """Verify _FieldDict returns values directly when the key is already present."""
    d = _FieldDict({"hashString": "abc", "download_dir": "/tmp"})
    assert d["hashString"] == "abc"  # exact hit
    assert d["download_dir"] == "/tmp"  # exact hit


def test_field_dict_missing_key_raises() -> None:
    """Verify _FieldDict raises KeyError for truly absent keys."""
    d = _FieldDict({"name": "test"})
    with pytest.raises(KeyError):
        _ = d["nonexistent"]


def test_field_dict_contains() -> None:
    """Verify __contains__ also uses snake_case fallback."""
    d = _FieldDict({"hash_string": "abc"})
    assert "hashString" in d  # camelCase lookup of snake_case key
    assert "hash_string" in d  # direct lookup
    assert "missing" not in d


def test_field_dict_get() -> None:
    """Verify .get() uses snake_case fallback and returns default for missing keys."""
    d = _FieldDict({"tracker_stats": []})
    assert d.get("trackerStats") == []  # camelCase → snake_case
    assert d.get("missing", 42) == 42


def test_container_uses_field_dict() -> None:
    """Verify Container wraps fields in _FieldDict so snake_case responses work."""
    # Simulate a JSON-RPC 2.0 response with snake_case keys
    c = Container(fields={"hash_string": "deadbeef", "download_dir": "/var/data"})
    # Property accessors use camelCase / kebab; _FieldDict makes them find snake_case
    assert c.fields["hashString"] == "deadbeef"
    assert c.fields["downloadDir"] == "/var/data"
    assert c.get("hashString") == "deadbeef"
    assert c.get("missing_key", "default") == "default"
