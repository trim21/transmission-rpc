import os
from unittest import mock

from transmission_rpc.client import Client

HOST = os.getenv('TR_HOST', '127.0.0.1')
PORT = int(os.getenv('TR_PORT', '9091'))
USER = os.getenv('TR_USER', 'admin')
PASSWORD = os.getenv('TR_PASSWORD', 'password')


def test_client_parse_url():
    with mock.patch('transmission_rpc.client.Client._request'):
        client = Client()
        assert client.url == 'http://127.0.0.1:9091/transmission/rpc'


def test_real_add_torrent():
    c = Client(host=HOST, port=PORT, username=USER, password=PASSWORD)
    torrent_url = 'magnet:?xt=urn:btih:e84213a794f3ccd890382a54a64ca68b7e925433'
    c.add_torrent(torrent_url)
    assert len(c.get_torrents()) > 0, 'transmission should has at least 1 task'
