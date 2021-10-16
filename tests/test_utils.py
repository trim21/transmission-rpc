# 2008-12, Erik Svensson <erik.public@gmail.com>
# Copyright (c) 2018-2020 Trim21 <i@trim21.me>
# Licensed under the MIT license.
import datetime

import pytest

from transmission_rpc import utils


def assert_almost_eq(value: float, expected: float):
    assert abs(value - expected) < 1


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
