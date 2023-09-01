import logging
import urllib.parse

from transmission_rpc.error import TransmissionError
from transmission_rpc.types import File, Group
from transmission_rpc.client import Client
from transmission_rpc.session import Session
from transmission_rpc.torrent import Torrent
from transmission_rpc.constants import LOGGER, DEFAULT_TIMEOUT, IdleMode, Priority, RatioLimitMode

__all__ = [
    "Client",
    "Group",
    "DEFAULT_TIMEOUT",
    "LOGGER",
    "TransmissionError",
    "Session",
    "Torrent",
    "File",
    "from_url",
    "Priority",
    "RatioLimitMode",
    "IdleMode",
]


def from_url(
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
    logger: logging.Logger = LOGGER,
) -> Client:
    """
    .. code-block:: python

        from_url("http://127.0.0.1/transmission/rpc")  # http://127.0.0.1:80/transmission/rpc
        from_url("https://127.0.0.1/transmission/rpc")  # https://127.0.0.1:443/transmission/rpc
        from_url("http://127.0.0.1")  # http://127.0.0.1:80/transmission/rpc
        from_url("http://127.0.0.1/")  # http://127.0.0.1:80/

    Warnings
    --------
        you can't ignore scheme, ``127.0.0.1:9091`` is not valid url, please use ``http://127.0.0.1:9091``

        And ``from_url("http://127.0.0.1")`` is not same as ``from_url("http://127.0.0.1/")``,
        ``path`` of ``http://127.0.0.1/`` is ``/``

    """
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
        path=u.path or "/transmission/rpc",
        timeout=timeout,
        logger=logger,
    )
