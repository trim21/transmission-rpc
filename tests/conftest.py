# ruff: noqa: SIM117
import contextlib
import os
import secrets
import socket
import time

import pytest

from transmission_rpc import LOGGER
from transmission_rpc.client import Client

PROTOCOL = os.getenv("TR_PROTOCOL", "http")
HOST = os.getenv("TR_HOST", "127.0.0.1")
PORT = int(os.getenv("TR_PORT", "9091"))
USER = os.getenv("TR_USER", "admin")
PASSWORD = os.getenv("TR_PASSWORD", "password")


def pytest_configure():
    start = time.time()
    while True:
        with contextlib.suppress(ConnectionError, FileNotFoundError):
            is_unix = PROTOCOL == "http+unix"
            with socket.socket(socket.AF_UNIX if is_unix else socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(3)
                sock.connect(HOST if is_unix else (HOST, PORT))
                break

        if time.time() - start > 30:
            raise ConnectionError("timeout trying to connect to transmission-daemon, is transmission daemon started?")


@pytest.fixture()
def tr_client():
    LOGGER.setLevel("INFO")
    with Client(protocol=PROTOCOL, host=HOST, port=PORT, username=USER, password=PASSWORD) as c:
        for torrent in c.get_torrents():
            c.remove_torrent(torrent.id, delete_data=True)
        yield c
        for torrent in c.get_torrents():
            c.remove_torrent(torrent.id, delete_data=True)


@pytest.fixture()
def fake_hash_factory():
    return lambda: secrets.token_hex(20)
