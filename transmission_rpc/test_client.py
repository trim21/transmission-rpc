import os

import pytest

from transmission_rpc.client import Client

TEST_HOST = os.getenv('TRANSMISSION_HOST', '127.0.0.1')
USERNAME = 'transmission-rpc-username'
PASSWORD = 'example-rpc-password'


@pytest.mark.parametrize(
    'kwargs', [
        Client(TEST_HOST, port=9091, user=USERNAME, password=PASSWORD),
    ]
)
def test_client_parse_url(kwargs):
    client = kwargs
    assert client.url == 'http://{}:9091/transmission/rpc'.format(TEST_HOST)
