import logging
import urllib.parse
from typing import Union

from transmission_rpc.error import TransmissionError
from transmission_rpc.types import File, Group
from transmission_rpc.client import Client
from transmission_rpc.session import Session
from transmission_rpc.torrent import Torrent
from transmission_rpc.constants import LOGGER, PRIORITY, RATIO_LIMIT, DEFAULT_TIMEOUT

__all__ = [
    "Client",
    "Group",
    "DEFAULT_TIMEOUT",
    "PRIORITY",
    "RATIO_LIMIT",
    "LOGGER",
    "TransmissionError",
    "Session",
    "Torrent",
    "File",
    "from_url",
]


def from_url(
    url: str,
    timeout: Union[int, float] = DEFAULT_TIMEOUT,
    logger: logging.Logger = LOGGER,
) -> Client:
    u = urllib.parse.urlparse(url)

    protocol = u.scheme
    if protocol == "http":
        default_port = 80
    elif protocol == "https":
        default_port = 443
    else:
        raise ValueError(f"unknown url scheme {u.scheme}")

    return Client(
        protocol=protocol,  # type: ignore
        username=u.username,
        password=u.password,
        host=u.hostname or "127.0.0.1",
        port=u.port or default_port,
        path=u.path,
        timeout=timeout,
        logger=logger,
    )
