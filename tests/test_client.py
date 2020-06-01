import os
import base64
import os.path
from unittest import mock

import pytest

from transmission_rpc.client import Client

HOST = os.getenv('TR_HOST', '127.0.0.1')
PORT = int(os.getenv('TR_PORT', '9091'))
USER = os.getenv('TR_USER', 'admin')
PASSWORD = os.getenv('TR_PASSWORD', 'password')


def test_client_parse_url():
    with mock.patch('transmission_rpc.client.Client._request'):
        client = Client()
        assert client.url == 'http://127.0.0.1:9091/transmission/rpc'


torrent_hash = 'e84213a794f3ccd890382a54a64ca68b7e925433'


@pytest.fixture()
def tr_client():
    with Client(host=HOST, port=PORT, username=USER, password=PASSWORD) as c:
        for torrent in c.get_torrents():
            c.remove_torrent(torrent.id)
        yield c
        for torrent in c.get_torrents():
            c.remove_torrent(torrent.id)


def test_real_add_magnet(tr_client: Client):
    torrent_url = 'magnet:?xt=urn:btih:e84213a794f3ccd890382a54a64ca68b7e925433'
    tr_client.add_torrent(torrent_url)
    assert len(tr_client.get_torrents()) == 1, 'transmission should has at least 1 task'


def test_real_add_torrent_fd(tr_client: Client):
    with open('tests/fixtures/iso.torrent', 'rb') as f:
        tr_client.add_torrent(f)
    assert len(tr_client.get_torrents()) == 1, 'transmission should has at least 1 task'


def test_real_add_torrent_base64(tr_client: Client):
    with open('tests/fixtures/iso.torrent', 'rb') as f:
        tr_client.add_torrent(base64.b64encode(f.read()).decode())
    assert len(tr_client.get_torrents()) == 1, 'transmission should has at least 1 task'


def test_real_add_torrent_file_protocol(tr_client: Client):
    fs = os.path.abspath(os.path.join(os.path.dirname(__file__, ), 'fixtures/iso.torrent'))
    tr_client.add_torrent('file://' + fs)
    assert len(tr_client.get_torrents()) == 1, 'transmission should has at least 1 task'


def test_real_add_torrent_http(tr_client: Client):
    tr_client.add_torrent(
        'https://releases.ubuntu.com/20.04/ubuntu-20.04-desktop-amd64.iso.torrent'
    )
    assert len(tr_client.get_torrents()) == 1, 'transmission should has at least 1 task'
