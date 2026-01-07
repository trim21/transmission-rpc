# ruff: noqa: SLF001, S108, S106, PT030
import importlib
import json
import socket
from typing import Any
from unittest import mock

import pytest
import urllib3
from urllib3 import Timeout

import transmission_rpc.client
from transmission_rpc import from_url
from transmission_rpc._unix_socket import UnixHTTPConnection, UnixHTTPConnectionPool
from transmission_rpc.client import Client


def test_client_init_invalid_protocol() -> None:
    with pytest.raises(ValueError, match="Unknown protocol"):
        Client(protocol="ftp")  # type: ignore[arg-type]


def test_client_init_logger_error() -> None:
    with pytest.raises(TypeError, match="logger must be instance"):
        Client(logger="not_a_logger")  # type: ignore[arg-type]


def test_timeout_property(client: Client) -> None:
    client.timeout = urllib3.Timeout(10.0)
    assert client.timeout is not None
    assert client.timeout.total == 10.0
    del client.timeout
    assert client.timeout is not None
    assert client.timeout.total == 30.0
    with pytest.raises(TypeError, match="must use Timeout instance"):
        client.timeout = 5.0  # type: ignore[assignment]


def test_deprecated_properties(client: Client) -> None:
    with pytest.warns(DeprecationWarning, match="do not use"):
        _ = client.url
    with pytest.warns(DeprecationWarning, match="do not use"):
        _ = client.torrent_get_arguments
    with pytest.warns(DeprecationWarning, match="do not use"):
        _ = client.raw_session
    with pytest.warns(DeprecationWarning, match="do not use"):
        _ = client.session_id
    with pytest.warns(DeprecationWarning, match="do not use"):
        _ = client.server_version
    with pytest.warns(DeprecationWarning, match="use .get_session"):
        _ = client.semver_version
    with pytest.warns(DeprecationWarning, match="use .get_session"):
        _ = client.rpc_version


def test_client_init_no_auth(mock_http_client: Any) -> None:
    c = Client(username=None, password=None)
    headers = c._Client__auth_headers  # type: ignore[attr-defined]
    assert "Authorization" not in headers


def test_client_init_timeout(mock_http_client: Any) -> None:
    c = Client(timeout=10.0)
    assert c.timeout is not None
    assert c.timeout.total == 10.0
    c2 = Client(timeout=10)
    assert c2.timeout is not None
    assert c2.timeout.total == 10.0


def test_client_init_timeout_types(mock_http_client: Any) -> None:
    c = Client(timeout=Timeout(10))
    assert c.timeout is not None
    assert c.timeout.total == 10

    c = Client(timeout=None)
    assert c.timeout is None

    with pytest.raises(TypeError, match="unsupported value"):
        Client(timeout="invalid")  # type: ignore[arg-type]


def test_context_manager_error(client: Client) -> None:
    with pytest.raises(ValueError, match="test"), client:
        raise ValueError("test")


def test_http_unix_init() -> None:
    """Cover initialization of http+unix protocol"""
    with (
        mock.patch("transmission_rpc.client.UnixHTTPConnectionPool"),
        mock.patch.object(Client, "get_session", autospec=True),
    ):
        c = Client(protocol="http+unix", host="/tmp/test", path="/transmission/")
        assert c._url == "http+unix://localhost:9091/transmission/rpc"


def test_import_error_version() -> None:
    """Cover the ImportError block for version retrieval"""
    with mock.patch("importlib.metadata.version", side_effect=ImportError):
        importlib.reload(transmission_rpc.client)
        assert transmission_rpc.client.__version__ == "develop"

    importlib.reload(transmission_rpc.client)


def test_deprecated_client_properties() -> None:
    """Cover deprecated properties"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        # Manually set private attributes that are usually set in init/get_session
        c._Client__semver_version = "1.0.0"  # type: ignore[attr-defined]
        c._Client__protocol_version = 15  # type: ignore[attr-defined]

        with pytest.warns(DeprecationWarning):
            assert c.semver_version == "1.0.0"
        with pytest.warns(DeprecationWarning):
            assert c.rpc_version == 15
        with pytest.warns(DeprecationWarning):
            assert c.url == c._url
        with pytest.warns(DeprecationWarning):
            assert c.session_id == "0"
        with pytest.warns(DeprecationWarning):
            assert c.server_version == "(unknown)"
        with pytest.warns(DeprecationWarning):
            assert c.torrent_get_arguments == c._Client__torrent_get_arguments  # type: ignore[attr-defined]
        with pytest.warns(DeprecationWarning):
            assert c.raw_session == {}


def test_timeout_property_mocked() -> None:
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client(timeout=10)
        assert isinstance(c.timeout, Timeout)

        c.timeout = Timeout(20)
        assert c.timeout.total == 20

        with pytest.raises(TypeError):
            c.timeout = 10  # type: ignore[assignment]

        del c.timeout
        assert c.timeout.total == 30.0  # Default


def test_client_init_variations() -> None:
    """Cover Client init branches"""
    with mock.patch.object(Client, "get_session", autospec=True):
        # timeout=None
        c = Client(timeout=None)
        assert c.timeout is None

        # timeout=Timeout object
        t = Timeout(10)
        c = Client(timeout=t)
        assert c.timeout is t

        # path fix
        c = Client(path="/transmission/")
        assert c._path == "/transmission/rpc"

        # Auth
        c = Client(username="u", password="p")

        # HTTPS
        with mock.patch("transmission_rpc.client.urllib3.HTTPSConnectionPool") as mock_https:
            c = Client(protocol="https")
            mock_https.assert_called()


def test_more_client_methods_lifecycle() -> None:
    """Cover remaining client methods (lifecycle parts)"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c._request = mock.Mock()  # type: ignore[method-assign] # Needed because session_close calls it

        # session_close
        c.session_close()

        # Context manager
        c.close = mock.Mock()  # type: ignore[method-assign]
        with c:
            pass
        c.close.assert_called()


def test_from_url_invalid_scheme() -> None:
    with pytest.raises(ValueError, match="unknown url scheme"):
        from_url("ftp://127.0.0.1")


def test_from_url_http_unix_no_host() -> None:
    with pytest.raises(ValueError, match=r"http\+unix URL is missing Unix socket path"):
        from_url("http+unix://")


def test_from_url_http() -> None:
    with mock.patch.object(Client, "get_session", autospec=True):
        c = from_url("http://127.0.0.1")
        assert ":80" in c._url


def test_from_url_https() -> None:
    # We need to mock HTTPSConnectionPool to avoid certifi errors or connection attempts
    with (
        mock.patch("transmission_rpc.client.urllib3.HTTPSConnectionPool"),
        mock.patch.object(Client, "get_session", autospec=True),
    ):
        c = from_url("https://127.0.0.1")
        assert ":443" in c._url


def test_from_url_http_unix() -> None:
    with (
        mock.patch("transmission_rpc.client.UnixHTTPConnectionPool"),
        mock.patch.object(Client, "get_session", autospec=True),
    ):
        c = from_url("http+unix://%2Ftmp%2Ftest")
        # host is unquoted to /tmp/test, but Client init uses localhost for _url host part
        assert "http+unix://localhost" in c._url


def test_unix_http_connection() -> None:
    conn = UnixHTTPConnection("/tmp/sock")
    with (
        mock.patch("socket.socket") as mock_socket_cls,
        mock.patch.object(socket, "AF_UNIX", create=True, new=1),
    ):
        mock_sock = mock_socket_cls.return_value
        conn.connect()
        mock_sock.connect.assert_called_with("/tmp/sock")


def test_unix_http_connection_options() -> None:
    # Test with socket options and timeout
    conn = UnixHTTPConnection(
        "/tmp/sock",
        socket_options=[(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)],
        timeout=10,
    )
    with (
        mock.patch("socket.socket") as mock_socket_cls,
        mock.patch.object(socket, "AF_UNIX", create=True, new=1),
    ):
        mock_sock = mock_socket_cls.return_value
        conn.connect()
        mock_sock.setsockopt.assert_called_with(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        mock_sock.settimeout.assert_called_with(10)
        mock_sock.connect.assert_called_with("/tmp/sock")


def test_unix_http_connection_pool_str() -> None:
    pool = UnixHTTPConnectionPool(host="/tmp/sock")
    assert str(pool) == "UnixHTTPConnectionPool(host=/tmp/sock)"


def test_context_manager_mocked() -> None:
    with mock.patch("transmission_rpc.client.urllib3.HTTPConnectionPool") as m:
        m.return_value.request.return_value = mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "0"},
            data=json.dumps(
                {"result": "success", "arguments": {"rpc-version": 17, "version": "4.0", "rpc-version-semver": "5.0"}}
            ).encode(),
        )
        with Client():
            pass
        m.return_value.close.assert_called()
