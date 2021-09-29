import os
import secrets
import contextlib
from unittest import mock

import pytest

from transmission_rpc import LOGGER
from transmission_rpc.client import Client

HOST = os.getenv("TR_HOST", "127.0.0.1")
PORT = int(os.getenv("TR_PORT", "9091"))
USER = os.getenv("TR_USER", "admin")
PASSWORD = os.getenv("TR_PASSWORD", "password")


@pytest.fixture()
def tr_client():
    LOGGER.setLevel("INFO")
    with Client(host=HOST, port=PORT, username=USER, password=PASSWORD) as c:
        for torrent in c.get_torrents():
            c.remove_torrent(torrent.id, delete_data=True)
        yield c
        for torrent in c.get_torrents():
            c.remove_torrent(torrent.id, delete_data=True)


@pytest.fixture()
def mock_client_factor():
    @contextlib.contextmanager
    def patch(data=None):
        LOGGER.setLevel("ERROR")

        def side_effect(method, *args, **kwargs):
            if method == "session-get":
                return {"version": "2.80 (hello)", "rpc-version": 14}
            return data or {}

        m = mock.Mock(side_effect=side_effect)
        with mock.patch("transmission_rpc.client.Client._request", m):
            yield m

    return patch


@pytest.fixture()
def fake_hash_factory():
    return lambda: secrets.token_hex(20)
