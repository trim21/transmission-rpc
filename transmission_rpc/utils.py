# Copyright (c) 2018-2021 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.
import base64
import datetime
import warnings
from typing import Any, Dict, List, Tuple, Union, TypeVar, BinaryIO, Callable, Optional
from urllib.parse import urlparse

from transmission_rpc import constants
from transmission_rpc.error import TransmissionVersionError
from transmission_rpc.constants import LOGGER, BaseType

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
    return "%d %02d:%02d:%02d" % (delta.days, hours, minutes, seconds)


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


def make_python_name(name: str) -> str:
    """
    Convert Transmission RPC name to python compatible name.
    """
    return name.replace("-", "_")


def make_rpc_name(name: str) -> str:
    """
    Convert python compatible name to Transmission RPC name.
    """
    return name.replace("_", "-")


def argument_value_convert(
    method: str,
    argument: str,
    value: Any,
    rpc_version: int,
) -> Tuple[str, Any]:
    """
    Check and fix Transmission RPC issues with regards to methods, arguments and values.
    """
    if method in ("torrent-add", "torrent-get", "torrent-set"):
        args = constants.TORRENT_ARGS[method[-3:]]
    elif method in ("session-get", "session-set"):
        args = constants.SESSION_ARGS[method[-3:]]
    else:
        raise ValueError('Method "%s" not supported' % (method))
    if argument in args:
        info = args[argument]
        invalid_version = True
        while invalid_version:
            invalid_version = False
            replacement = None
            if rpc_version < info[1]:
                invalid_version = True
                replacement = info[3]
            if info[2] is not None and info[2] <= rpc_version:
                invalid_version = True
                replacement = info[4]
            if invalid_version:
                if replacement:
                    LOGGER.warning(
                        'Replacing requested argument "%s" with "%s".',
                        argument,
                        replacement,
                    )
                    argument = replacement
                    info = args[argument]
                else:
                    raise ValueError(
                        f'Method "{method}" Argument "{argument}" does not exist in version {rpc_version:d}.'
                    )
        return argument, TR_TYPE_MAP[info[0]](value)
    raise ValueError(f'Argument "{argument}" does not exists for method "{method}".')


def get_arguments(method: str, rpc_version: int) -> List[str]:
    """
    Get arguments for method in specified Transmission RPC version.
    """
    if method in ("torrent-add", "torrent-get", "torrent-set"):
        args = constants.TORRENT_ARGS[method[-3:]]
    elif method in ("session-get", "session-set"):
        args = constants.SESSION_ARGS[method[-3:]]
    else:
        raise ValueError('Method "%s" not supported' % (method))
    accessible = []
    for argument, info in args.items():
        valid_version = True
        if rpc_version < info[1]:
            valid_version = False
        if info[2] is not None and info[2] <= rpc_version:
            valid_version = False
        if valid_version:
            accessible.append(argument)
    return accessible


_Fn = TypeVar("_Fn")


def _rpc_version_check(method: str, kwargs: Dict[str, Any], rpc_version: int) -> None:
    if method in ("torrent-add", "torrent-get", "torrent-set"):
        rpc_args = constants.TORRENT_ARGS[method[-3:]]
    elif method in ("session-get", "session-set"):
        rpc_args = constants.SESSION_ARGS[method[-3:]]
    else:
        raise ValueError(f'Method "{method}" not supported')

    for key, arg in rpc_args.items():
        if key in kwargs and arg.added_version > rpc_version:
            raise TransmissionVersionError(
                f'Method "{method}" Argument "{key}" does not exist in version {rpc_version}'
            )


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

        if parsed_uri.scheme in ["file"]:
            warnings.warn(
                "support for `file://` URL is deprecated.", DeprecationWarning
            )
            filepath = torrent
            # uri decoded different on linux / windows ?
            if len(parsed_uri.path) > 0:
                filepath = parsed_uri.path
            elif len(parsed_uri.netloc) > 0:
                filepath = parsed_uri.netloc
            with open(filepath, "rb") as torrent_file:
                return base64.b64encode(torrent_file.read()).decode("utf-8")

        # maybe it's base64 encoded file content
        try:
            # check if this is base64 data
            base64.b64decode(torrent.encode("utf-8"), validate=True)
            return torrent
        except (TypeError, ValueError):
            pass

    elif isinstance(torrent, bytes):
        return base64.b64encode(torrent).decode("utf-8")
    # maybe a file, try read content and encode it.
    elif hasattr(torrent, "read"):
        return base64.b64encode(torrent.read()).decode("utf-8")

    return None
