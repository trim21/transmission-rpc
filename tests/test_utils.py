# 2008-12, Erik Svensson <erik.public@gmail.com>
# Copyright (c) 2018-2020 Trim21 <i@trim21.me>
# Licensed under the MIT license.
import datetime

import pytest

from transmission_rpc import utils


def assert_almost_eq(value: float, expected: float):
    assert abs(value - expected) < 1


@pytest.mark.parametrize(
    ("size", "expected"),
    {
        512: (512, "B"),
        1024: (1.0, "KiB"),
        1048575: (1023.999, "KiB"),
        1048576: (1.0, "MiB"),
        1073741824: (1.0, "GiB"),
        1099511627776: (1.0, "TiB"),
        1125899906842624: (1.0, "PiB"),
        1152921504606846976: (1.0, "EiB"),
    }.items(),
)
def test_format_size(size, expected):
    result = utils.format_size(size)
    assert_almost_eq(result[0], expected[0])
    assert result[1] == expected[1]


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (512, (512, "B/s")),
        (1024, (1.0, "KiB/s")),
        (1048575, (1023.999, "KiB/s")),
        (1048576, (1.0, "MiB/s")),
        (1073741824, (1.0, "GiB/s")),
        (1099511627776, (1.0, "TiB/s")),
        (1125899906842624, (1.0, "PiB/s")),
        (1152921504606846976, (1.0, "EiB/s")),
    ],
)
def test_format_speed(size, expected):
    result = utils.format_speed(size)
    assert_almost_eq(result[0], expected[0])
    assert result[1] == expected[1]


@pytest.mark.parametrize(
    ("delta", "expected"),
    {
        datetime.timedelta(0, 0): "0 00:00:00",
        datetime.timedelta(0, 10): "0 00:00:10",
        datetime.timedelta(0, 60): "0 00:01:00",
        datetime.timedelta(0, 61): "0 00:01:01",
        datetime.timedelta(0, 3661): "0 01:01:01",
        datetime.timedelta(1, 3661): "1 01:01:01",
        datetime.timedelta(13, 65660): "13 18:14:20",
    }.items(),
)
def test_format_timedelta(delta, expected):
    assert utils.format_timedelta(delta), expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, 0),
        (1, 1),
        (1000, 1),
        ("true", 1),
        ("Yes", 1),
        ("truE", 1),
        ("baka", 0),
        ("false", 0),
        ("no", 0),
        (True, 1),
        (False, 0),
    ],
)
def test_rpc_bool(value, expected):
    assert utils.rpc_bool(value) == expected, f"{value} should be convert to {expected}"
