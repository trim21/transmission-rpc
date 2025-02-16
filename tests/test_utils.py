# 2008-12, Erik Svensson <erik.public@gmail.com>
# Copyright (c) 2018-2020 Trim21 <i@trim21.me>
# Licensed under the MIT license.
from __future__ import annotations

import datetime
from typing import Any
from unittest import mock

import pytest

from transmission_rpc import DEFAULT_TIMEOUT, from_url, utils
from transmission_rpc.constants import LOGGER


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


@pytest.mark.parametrize(
    ("url", "kwargs"),
    {
        "http://a:b@127.0.0.1:9092/transmission/rpc": {
            "protocol": "http",
            "username": "a",
            "password": "b",
            "host": "127.0.0.1",
            "port": 9092,
            "path": "/transmission/rpc",
        },
        "http://127.0.0.1/transmission/rpc": {
            "protocol": "http",
            "username": None,
            "password": None,
            "host": "127.0.0.1",
            "port": 80,
            "path": "/transmission/rpc",
        },
        "https://127.0.0.1/tr/transmission/rpc": {
            "protocol": "https",
            "username": None,
            "password": None,
            "host": "127.0.0.1",
            "port": 443,
            "path": "/tr/transmission/rpc",
        },
        "https://127.0.0.1/": {
            "protocol": "https",
            "username": None,
            "password": None,
            "host": "127.0.0.1",
            "port": 443,
            "path": "/",
        },
        "http+unix://%2Fvar%2Frun%2Ftransmission.sock/transmission/rpc": {
            "protocol": "http+unix",
            "username": None,
            "password": None,
            "host": "/var/run/transmission.sock",
            "port": None,
            "path": "/transmission/rpc",
        },
    }.items(),
)
def test_from_url(url: str, kwargs: dict[str, Any]):
    with mock.patch("transmission_rpc.Client") as m:
        from_url(url)
        m.assert_called_once_with(
            **kwargs,
            timeout=DEFAULT_TIMEOUT,
            logger=LOGGER,
        )
