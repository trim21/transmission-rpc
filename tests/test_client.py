from unittest import mock

from transmission_rpc.client import Client


def test_client_parse_url():
    with mock.patch('transmission_rpc.client.Client._request'):
        client = Client()
        assert client.url == 'http://127.0.0.1:9091/transmission/rpc'
