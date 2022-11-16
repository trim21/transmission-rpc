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
    port = u.port
    if port is None:
        if u.scheme == "http":
            port = 80
        elif u.scheme == "https":
            port = 443
        else:
            raise ValueError(f"unknown url scheme {u.scheme}")

    return Client(
        protocol=u.scheme,
        username=u.username,
        password=u.password,
        host=u.hostname,
        port=port,
        path=u.path,
        timeout=timeout,
        logger=logger,
    )
