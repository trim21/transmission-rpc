import contextlib
import os
import secrets
import socket
import time
from collections.abc import Callable, Generator
from typing import Literal, cast

import pytest

from transmission_rpc import LOGGER
from transmission_rpc.client import Client


@pytest.fixture(scope="session")
def wait_for_transmission() -> None:
    """
    Waits for the Transmission daemon to be available.

    This fixture is session-scoped, so it runs once per test session,
    but only if a test actually requests it (directly or indirectly).
    """
    protocol = os.environ["TR_PROTOCOL"]
    host = os.environ["TR_HOST"]
    port = int(os.environ["TR_PORT"])

    start = time.time()
    while True:
        with contextlib.suppress(ConnectionError, FileNotFoundError):
            is_unix = protocol == "http+unix"
            with socket.socket(socket.AF_UNIX if is_unix else socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(3)
                sock.connect(host if is_unix else (host, port))
                break

        if time.time() - start > 30:
            raise ConnectionError("timeout trying to connect to transmission-daemon, is transmission daemon started?")


@pytest.fixture
def tr_client(wait_for_transmission: None) -> Generator[Client, None, None]:
    """
    Provides a Client instance connected to the Transmission daemon.

    This fixture cleans up torrents before and after the test.
    It depends on 'wait_for_transmission' to ensure the daemon is reachable.
    """
    LOGGER.setLevel("INFO")
    # Cast TR_PROTOCOL to the Literal type expected by Client
    protocol_arg = cast("Literal['http', 'https', 'http+unix']", os.environ["TR_PROTOCOL"])
    host = os.environ["TR_HOST"]
    port = int(os.environ["TR_PORT"])
    with Client(
        protocol=protocol_arg,
        host=host,
        port=port,
        username=os.environ["TR_USER"],
        password=os.environ["TR_PASSWORD"],
    ) as c:
        for torrent in c.get_torrents():
            c.remove_torrent(torrent.id, delete_data=True)
        yield c
        for torrent in c.get_torrents():
            c.remove_torrent(torrent.id, delete_data=True)


@pytest.fixture
def generate_random_hash() -> Callable[[], str]:
    """Generates a random SHA1 hash string for testing."""
    return lambda: secrets.token_hex(20)
