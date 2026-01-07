import json
from collections.abc import Generator
from typing import Any
from unittest import mock

import pytest

from transmission_rpc.client import Client


@pytest.fixture
def mock_http_client() -> Generator[mock.MagicMock, None, None]:
    with mock.patch("transmission_rpc.client.urllib3.HTTPConnectionPool") as m:
        m.return_value.request.return_value = mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "session_id"},
            data=json.dumps(
                {
                    "result": "success",
                    "arguments": {"rpc-version": 17, "rpc-version-semver": "5.3.0", "version": "4.0.0"},
                }
            ).encode("utf-8"),
        )
        yield m


@pytest.fixture
def client(mock_http_client: Any) -> Client:
    return Client()
