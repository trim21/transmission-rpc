from __future__ import annotations

import importlib
import json
import socket
from typing import Any, Literal
from unittest import mock
from urllib.parse import urljoin

import pytest
import urllib3
from urllib3 import Timeout

import transmission_rpc.client
from transmission_rpc import DEFAULT_TIMEOUT, from_url
from transmission_rpc._unix_socket import UnixHTTPConnection, UnixHTTPConnectionPool
from transmission_rpc.client import Client
from transmission_rpc.constants import LOGGER
from transmission_rpc.error import TransmissionAuthError


@pytest.mark.parametrize(
    ("url", "kwargs"),
    list(
        {
            "http://a:b@127.0.0.1:9092/transmission/rpc": {
                "protocol": "http",
                "username": "a",
                "password": "b",
                "host": "127.0.0.1",
                "port": 9092,
                "path": "/transmission/rpc",
            },
            "http://127.0.0.1/transmission/rpc": {
                "protocol": "http",
                "username": None,
                "password": None,
                "host": "127.0.0.1",
                "port": 80,
                "path": "/transmission/rpc",
            },
            "https://127.0.0.1/tr/transmission/rpc": {
                "protocol": "https",
                "username": None,
                "password": None,
                "host": "127.0.0.1",
                "port": 443,
                "path": "/tr/transmission/rpc",
            },
            "https://127.0.0.1/": {
                "protocol": "https",
                "username": None,
                "password": None,
                "host": "127.0.0.1",
                "port": 443,
                "path": "/",
            },
            "http+unix://%2Fvar%2Frun%2Ftransmission.sock/transmission/rpc": {
                "protocol": "http+unix",
                "username": None,
                "password": None,
                "host": "/var/run/transmission.sock",
                "port": None,
                "path": "/transmission/rpc",
            },
        }.items()
    ),
)
def test_from_url(url: str, kwargs: dict[str, Any]) -> None:
    """
    Verify that `from_url` correctly parses URLs and initializes the Client with the expected arguments.
    """
    with mock.patch("transmission_rpc.Client") as m:
        from_url(url)
        m.assert_called_once_with(
            **kwargs,
            timeout=DEFAULT_TIMEOUT,
            logger=LOGGER,
        )


def test_client_init_invalid_protocol() -> None:
    """Verify that initializing Client with an invalid protocol raises a ValueError."""
    with pytest.raises(ValueError, match="Unknown protocol"):
        Client(protocol="ftp")  # type: ignore[arg-type]


def test_client_init_logger_error() -> None:
    """Verify that initializing Client with a non-logger object raises a TypeError."""
    with pytest.raises(TypeError, match="logger must be instance"):
        Client(logger="not_a_logger")  # type: ignore[arg-type]


def test_timeout_property(client: Client) -> None:
    """
    Verify that the 'timeout' property works correctly:
    - Setting it updates the internal timeout.
    - Deleting it resets it to the default.
    - Setting an invalid type raises TypeError.
    """
    client.timeout = urllib3.Timeout(10.0)
    assert client.timeout is not None
    assert client.timeout.total == 10.0
    del client.timeout
    assert client.timeout is not None
    assert client.timeout.total == 30.0
    with pytest.raises(TypeError, match="must use Timeout instance"):
        client.timeout = 5.0  # type: ignore[assignment]


def test_deprecated_properties(client: Client) -> None:
    """Verify that accessing deprecated properties emits a DeprecationWarning and returns expected values."""
    with pytest.warns(DeprecationWarning, match="do not use"):
        assert client.url == client._url  # noqa: SLF001
    with pytest.warns(DeprecationWarning, match="do not use"):
        assert client.torrent_get_arguments == client._Client__torrent_get_arguments  # type: ignore[attr-defined] # noqa: SLF001
    with pytest.warns(DeprecationWarning, match="do not use"):
        # The raw_session is populated by get_session() which is called in client init.
        # The fixture mock returns specific session data.
        assert "version" in client.raw_session
    with pytest.warns(DeprecationWarning, match="do not use"):
        assert client.session_id == "session_id"
    with pytest.warns(DeprecationWarning, match="do not use"):
        assert client.server_version == "4.0.0"
    with pytest.warns(DeprecationWarning, match="use .get_session"):
        assert client.semver_version == "5.3.0"
    with pytest.warns(DeprecationWarning, match="use .get_session"):
        assert client.rpc_version == 17


def test_client_init_no_auth(mock_http_client: Any) -> None:
    """Verify that initializing Client without credentials does not set the Authorization header."""
    c = Client(username=None, password=None)
    headers = c._Client__auth_headers  # type: ignore[attr-defined]  # noqa: SLF001
    assert "Authorization" not in headers


def test_client_init_timeout_parsing(mock_http_client: Any) -> None:
    """
    Verify that initializing Client with different timeout types (float, int, Timeout object, None)
    behaves as expected, and raises TypeError for invalid types.
    """
    # Float
    c = Client(timeout=10.0)
    assert c.timeout is not None
    assert c.timeout.total == 10.0

    # Int
    c = Client(timeout=10)
    assert c.timeout is not None
    assert c.timeout.total == 10.0

    # Timeout object
    c = Client(timeout=Timeout(10))
    assert c.timeout is not None
    assert c.timeout.total == 10

    # None
    c = Client(timeout=None)
    assert c.timeout is None

    # Invalid
    with pytest.raises(TypeError, match="unsupported value"):
        Client(timeout="invalid")  # type: ignore[arg-type]


def test_context_manager_error(client: Client) -> None:
    """Verify that exceptions raised within the Client context manager are propagated."""
    with pytest.raises(ValueError, match="test"), client:
        raise ValueError("test")


def test_http_unix_init() -> None:
    """Cover initialization of http+unix protocol to ensure correct URL construction."""
    with (
        mock.patch("transmission_rpc.client.UnixHTTPConnectionPool"),
        mock.patch.object(Client, "get_session", autospec=True),
    ):
        c = Client(protocol="http+unix", host="/tmp/test", path="/transmission/")  # noqa: S108
        assert c._url == "http+unix://localhost:9091/transmission/rpc"  # noqa: SLF001


def test_import_error_version() -> None:
    """Cover the ImportError block for version retrieval to ensure fallback to 'develop'."""
    with mock.patch("importlib.metadata.version", side_effect=ImportError):
        importlib.reload(transmission_rpc.client)
        assert transmission_rpc.client.__version__ == "develop"

    importlib.reload(transmission_rpc.client)


def test_client_init_edge_cases() -> None:
    """Cover Client init branches including timeout=None, path correction, and HTTPS protocol."""
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
        assert c._path == "/transmission/rpc"  # noqa: SLF001

        # Auth
        c = Client(username="u", password="p")  # noqa: S106

        # HTTPS
        with mock.patch("transmission_rpc.client.urllib3.HTTPSConnectionPool") as mock_https:
            c = Client(protocol="https")
            mock_https.assert_called()


def test_session_close_and_context_manager() -> None:
    """Cover remaining client methods (lifecycle parts) like session_close and context manager behavior."""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c._request = mock.Mock()  # type: ignore[method-assign] # Needed because session_close calls it  # noqa: SLF001

        # session_close
        c.session_close()

        # Context manager
        c.close = mock.Mock()  # type: ignore[method-assign]
        with c:
            pass
        c.close.assert_called()


def test_from_url_invalid_scheme() -> None:
    """Verify `from_url` raises ValueError for unknown URL schemes."""
    with pytest.raises(ValueError, match="unknown url scheme"):
        from_url("ftp://127.0.0.1")


def test_from_url_http_unix_no_host() -> None:
    """Verify `from_url` raises ValueError for http+unix URLs missing the socket path."""
    with pytest.raises(ValueError, match=r"http\+unix URL is missing Unix socket path"):
        from_url("http+unix://")


def test_from_url_http() -> None:
    """Verify `from_url` correctly parses standard HTTP URLs."""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = from_url("http://127.0.0.1")
        assert ":80" in c._url  # noqa: SLF001


def test_from_url_https() -> None:
    """Verify `from_url` correctly parses HTTPS URLs."""
    # We need to mock HTTPSConnectionPool to avoid certifi errors or connection attempts
    with (
        mock.patch("transmission_rpc.client.urllib3.HTTPSConnectionPool"),
        mock.patch.object(Client, "get_session", autospec=True),
    ):
        c = from_url("https://127.0.0.1")
        assert ":443" in c._url  # noqa: SLF001


def test_from_url_http_unix() -> None:
    """Verify `from_url` correctly parses http+unix URLs."""
    with (
        mock.patch("transmission_rpc.client.UnixHTTPConnectionPool"),
        mock.patch.object(Client, "get_session", autospec=True),
    ):
        c = from_url("http+unix://%2Ftmp%2Ftest")
        # host is unquoted to /tmp/test, but Client init uses localhost for _url host part
        assert "http+unix://localhost" in c._url  # noqa: SLF001


def test_unix_http_connection() -> None:
    """Verify `UnixHTTPConnection` connects to the correct socket path."""
    conn = UnixHTTPConnection("/tmp/sock")  # noqa: S108
    with (
        mock.patch("socket.socket") as mock_socket_cls,
        mock.patch.object(socket, "AF_UNIX", create=True, new=1),
    ):
        mock_sock = mock_socket_cls.return_value
        conn.connect()
        mock_sock.connect.assert_called_with("/tmp/sock")  # noqa: S108


def test_unix_http_connection_options() -> None:
    """Verify `UnixHTTPConnection` respects socket options and timeouts."""
    # Test with socket options and timeout
    conn = UnixHTTPConnection(
        "/tmp/sock",  # noqa: S108
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
        mock_sock.connect.assert_called_with("/tmp/sock")  # noqa: S108


def test_unix_http_connection_pool_str() -> None:
    """Verify `UnixHTTPConnectionPool` string representation."""
    pool = UnixHTTPConnectionPool(host="/tmp/sock")  # noqa: S108
    assert str(pool) == "UnixHTTPConnectionPool(host=/tmp/sock)"


def test_context_manager_mocked() -> None:
    """Verify that the Client properly closes connections when used as a context manager."""
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


@pytest.mark.parametrize(
    ("protocol", "username", "password", "host", "port", "path"),
    [
        (
            "https",
            "a+2da/s a?s=d$",
            "a@as +@45/:&*^",
            "127.0.0.1",
            2333,
            "/transmission/",
        ),
        (
            "http",
            "/",
            None,
            "127.0.0.1",
            2333,
            "/transmission/",
        ),
    ],
)
def test_client_parse_url(
    protocol: Literal["http", "https"], username: str, password: str | None, host: str, port: int, path: str
) -> None:
    """
    Verify that the Client correctly parses the URL from the given parameters.
    """
    with (
        mock.patch.object(Client, "_request"),
        mock.patch.object(Client, "get_session"),
    ):
        client = Client(
            protocol=protocol,
            username=username,
            password=password,
            host=host,
            port=port,
            path=path,
        )

        assert client._url == f"{protocol}://{host}:{port}{urljoin(path, 'rpc')}"  # noqa: SLF001


@pytest.mark.parametrize(
    "status_code",
    [401, 403],
)
def test_raise_unauthorized(status_code: int) -> None:
    """
    Verify that Client raises TransmissionAuthError when the server returns 401 or 403.
    """
    m = mock.Mock(return_value=mock.Mock(status=status_code))
    with mock.patch("urllib3.HTTPConnectionPool.request", m), pytest.raises(TransmissionAuthError):
        Client()
