import logging
import urllib.parse

from transmission_rpc.client import DEFAULT_TIMEOUT, Client
from transmission_rpc.constants import LOGGER, IdleMode, Priority, RatioLimitMode
from transmission_rpc.error import (
    TransmissionAuthError,
    TransmissionConnectError,
    TransmissionError,
    TransmissionTimeoutError,
)
from transmission_rpc.session import Session, SessionStats, Stats
from transmission_rpc.torrent import FileStat, Status, Torrent, Tracker, TrackerStats
from transmission_rpc.types import File, Group, PortTestResult

__all__ = [
    "DEFAULT_TIMEOUT",
    "LOGGER",
    "Client",
    "File",
    "FileStat",
    "Group",
    "IdleMode",
    "PortTestResult",
    "Priority",
    "RatioLimitMode",
    "Session",
    "SessionStats",
    "Stats",
    "Status",
    "Torrent",
    "Tracker",
    "TrackerStats",
    "TransmissionAuthError",
    "TransmissionConnectError",
    "TransmissionError",
    "TransmissionTimeoutError",
    "from_url",
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
        from_url("http+unix://%2Fvar%2Frun%2Ftransmission.sock/transmission/rpc")  # /transmission/rpc on /var/run/transmission.sock Unix socket

    Warnings:
        you can't ignore scheme, ``127.0.0.1:9091`` is not valid url, please use ``http://127.0.0.1:9091``

        And ``from_url("http://127.0.0.1")`` is not same as ``from_url("http://127.0.0.1/")``,
        ``path`` of ``http://127.0.0.1/`` is ``/``

    """
    u = urllib.parse.urlparse(url)

    protocol = u.scheme
    host = u.hostname
    default_port = None
    if protocol == "http":
        default_port = 80
    elif protocol == "https":
        default_port = 443
    elif protocol == "http+unix":
        if host is None:
            raise ValueError("http+unix URL is missing Unix socket path")
        host = urllib.parse.unquote(host, errors="strict")
    else:
        raise ValueError(f"unknown url scheme {u.scheme}")

    return Client(
        protocol=protocol,  # type: ignore
        username=u.username,
        password=u.password,
        host=host or "127.0.0.1",
        port=u.port or default_port,
        path=u.path or "/transmission/rpc",
        timeout=timeout,
        logger=logger,
    )
