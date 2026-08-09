# Copyright (c) 2018-2021 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.
from __future__ import annotations

import base64
import datetime
import pathlib
from typing import BinaryIO
from urllib.parse import urlparse

from typing_extensions import deprecated

from transmission_rpc import constants

UNITS = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB"]


def _format_size(size: int) -> tuple[float, str]:
    """
    Format byte size into IEC prefixes, B, KiB, MiB ...
    """
    s = float(size)
    i = 0
    while s >= 1024.0 and i < len(UNITS):
        i += 1
        s /= 1024.0
    return s, UNITS[i]


@deprecated("will be removed in v8 without replacement")
def format_size(size: int) -> tuple[float, str]:
    """Format byte size into IEC prefixes, B, KiB, MiB ..."""
    return _format_size(size)


@deprecated("will be removed in v8 without replacement")
def format_speed(size: int) -> tuple[float, str]:
    """
    Format bytes per second speed into IEC prefixes, B/s, KiB/s, MiB/s ...
    """
    (s, unit) = _format_size(size)
    return s, f"{unit}/s"


def format_timedelta(delta: datetime.timedelta) -> str:
    """
    Format datetime.timedelta into <days> <hours>:<minutes>:<seconds>.
    """
    minutes, seconds = divmod(delta.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{delta.days:d} {hours:02d}:{minutes:02d}:{seconds:02d}"


@deprecated("import get_torrent_arguments from transmission_rpc.constants instead")
def get_torrent_arguments(rpc_version: int) -> list[str]:
    """Compatibility import for :func:`transmission_rpc.constants.get_torrent_arguments`."""
    return constants.get_torrent_arguments(rpc_version)


def _try_read_torrent(torrent: BinaryIO | str | bytes | pathlib.Path) -> str | None:
    """
    if torrent should be encoded with base64, return a non-None value.
    """
    # torrent is a str, may be a url
    if isinstance(torrent, str):
        parsed_uri = urlparse(torrent)
        # torrent starts with file, read from local disk and encode it to base64 url.
        if parsed_uri.scheme in ["https", "http", "magnet"]:
            return None

        if parsed_uri.scheme in ["file"]:
            raise ValueError("support for `file://` URL has been removed.")
    elif isinstance(torrent, pathlib.Path):
        return base64.b64encode(torrent.read_bytes()).decode("utf-8")
    elif isinstance(torrent, bytes):
        return base64.b64encode(torrent).decode("utf-8")
    # maybe a file, try read content and encode it.
    elif hasattr(torrent, "read"):
        return base64.b64encode(torrent.read()).decode("utf-8")

    return None
