# Copyright (c) 2018-2021 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.
import base64
import datetime
from typing import Any, Dict, List, Tuple, Union, TypeVar, BinaryIO, Callable, Optional
from urllib.parse import urlparse

from transmission_rpc import constants
from transmission_rpc.constants import BaseType

UNITS = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB"]


def format_size(size: int) -> Tuple[float, str]:
    """
    Format byte size into IEC prefixes, B, KiB, MiB ...
    """
    s = float(size)
    i = 0
    while s >= 1024.0 and i < len(UNITS):
        i += 1
        s /= 1024.0
    return s, UNITS[i]


def format_speed(size: int) -> Tuple[float, str]:
    """
    Format bytes per second speed into IEC prefixes, B/s, KiB/s, MiB/s ...
    """
    (s, unit) = format_size(size)
    return s, unit + "/s"


def format_timedelta(delta: datetime.timedelta) -> str:
    """
    Format datetime.timedelta into <days> <hours>:<minutes>:<seconds>.
    """
    minutes, seconds = divmod(delta.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{delta.days:d} {hours:02d}:{minutes:02d}:{seconds:02d}"


def rpc_bool(arg: Any) -> int:
    """
    Convert between Python boolean and Transmission RPC boolean.
    """
    if isinstance(arg, str):
        try:
            arg = bool(int(arg))
        except ValueError:
            arg = arg.lower() in ["true", "yes"]
    return 1 if bool(arg) else 0


TR_TYPE_MAP: Dict[str, Callable] = {
    BaseType.number: int,
    BaseType.string: str,
    BaseType.double: float,
    BaseType.boolean: rpc_bool,
    BaseType.array: list,
    BaseType.object: dict,
}


def get_arguments(method: str, rpc_version: int) -> List[str]:
    """
    Get arguments for method in specified Transmission RPC version.
    """
    if method in ("torrent-add", "torrent-get", "torrent-set"):
        args = constants.TORRENT_ARGS[method[-3:]]
    elif method in ("session-get", "session-set"):
        args = constants.SESSION_ARGS[method[-3:]]
    else:
        raise ValueError(f'Method "{method}" not supported')
    accessible = []
    for argument, info in args.items():
        valid_version = True
        if rpc_version < info.added_version:
            valid_version = False
        if info.removed_version is not None and info.removed_version <= rpc_version:
            valid_version = False
        if valid_version:
            accessible.append(argument)
    return accessible


_Fn = TypeVar("_Fn")


def _try_read_torrent(torrent: Union[BinaryIO, str, bytes]) -> Optional[str]:
    """
    if torrent should be encoded with base64, return a non-None value.
    """
    # torrent is a str, may be a url
    if isinstance(torrent, str):
        parsed_uri = urlparse(torrent)
        # torrent starts with file, read from local disk and encode it to base64 url.
        if parsed_uri.scheme in ["https", "http", "magnet"]:
            return None

    elif isinstance(torrent, bytes):
        return base64.b64encode(torrent).decode("utf-8")
    # maybe a file, try read content and encode it.
    elif hasattr(torrent, "read"):
        return base64.b64encode(torrent.read()).decode("utf-8")

    return None


def _camel_to_snake(camel):
    snake = [camel[0].lower()]
    for c in camel[1:]:
        if c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            snake.append("_")
            snake.append(c.lower())
        else:
            snake.append(c)
    return str.join("", snake)
