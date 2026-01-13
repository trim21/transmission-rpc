from __future__ import annotations

import datetime

import pytest

from transmission_rpc import utils


@pytest.mark.parametrize(
    ("delta", "expected"),
    [
        (datetime.timedelta(0, 0), "0 00:00:00"),
        (datetime.timedelta(0, 10), "0 00:00:10"),
        (datetime.timedelta(0, 60), "0 00:01:00"),
        (datetime.timedelta(0, 61), "0 00:01:01"),
        (datetime.timedelta(0, 3661), "0 01:01:01"),
        (datetime.timedelta(1, 3661), "1 01:01:01"),
        (datetime.timedelta(13, 65660), "13 18:14:20"),
    ],
)
def test_format_timedelta(delta: datetime.timedelta, expected: str) -> None:
    """
    Verify that `format_timedelta` formats timedelta objects into strings as expected.
    """
    assert utils.format_timedelta(delta) == expected
