import contextlib
from typing import Any
from unittest import mock

import pytest

from transmission_rpc.constants import Args, Type, get_torrent_arguments
from transmission_rpc.error import TransmissionError
from transmission_rpc.torrent import Peer, PeersFrom, Tracker, TrackerStats
from transmission_rpc.types import BitMap, Container, Group, PortTestResult


def check_properties(cls: type, obj: Any) -> None:
    for prop in dir(cls):
        if isinstance(getattr(cls, prop), property):
            with contextlib.suppress(KeyError, DeprecationWarning):
                getattr(obj, prop)


def test_container_repr() -> None:
    """Test Container.__repr__ which is missing coverage."""
    c = Container(fields={"key": "value"})
    assert repr(c) == "<Container fields={'key': 'value'}>"


def test_peer_properties_access() -> None:
    p = Peer(fields={})
    check_properties(Peer, p)


def test_peers_from_properties_access() -> None:
    p = PeersFrom(fields={})
    check_properties(PeersFrom, p)


def test_tracker_properties_access() -> None:
    t = Tracker(fields={})
    check_properties(Tracker, t)


def test_tracker_stats_properties_access() -> None:
    t = TrackerStats(fields={})
    check_properties(TrackerStats, t)


def test_group_properties() -> None:
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
    fields = {"port-is-open": True, "ip_protocol": "ipv4"}
    r = PortTestResult(fields=fields)
    assert r.port_is_open is True
    assert r.ip_protocol == "ipv4"


def test_bitmap() -> None:
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
    arg = Args(Type.number, 1, description="desc")
    assert repr(arg) == "Args('number', 1, None, None, None, 'desc')"
    assert str(arg) == "Args<type=number, 1, description='desc')"


def test_get_torrent_arguments() -> None:
    args = get_torrent_arguments(1)
    assert "id" in args
    assert "group" not in args  # added in 17


def test_error_str_with_original() -> None:
    original = mock.Mock()
    original.__str__ = mock.Mock(return_value="original error")  # type: ignore[method-assign]
    type(original).__name__ = "OriginalError"
    err = TransmissionError("message", original=original)
    assert str(err) == 'message Original exception: OriginalError, "original error"'


def test_deprecated_raw_response() -> None:
    err = TransmissionError("message", raw_response="raw")
    with pytest.warns(DeprecationWarning, match="use .raw_response instead"):
        assert err.rawResponse == "raw"
