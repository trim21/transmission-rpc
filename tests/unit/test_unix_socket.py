import pathlib
import socket
from unittest import mock

from transmission_rpc._unix_socket import UnixHTTPConnection, UnixHTTPConnectionPool


def test_unix_http_connection(tmp_path: pathlib.Path) -> None:
    """Verify `UnixHTTPConnection` connects to the correct socket path."""
    socket_path = str(tmp_path / "sock")
    conn = UnixHTTPConnection(socket_path)
    with (
        mock.patch("socket.socket") as mock_socket_cls,
        mock.patch.object(socket, "AF_UNIX", create=True, new=1),
    ):
        mock_sock = mock_socket_cls.return_value
        conn.connect()
        mock_sock.connect.assert_called_with(socket_path)


def test_unix_http_connection_options(tmp_path: pathlib.Path) -> None:
    """Verify `UnixHTTPConnection` respects socket options and timeouts."""
    socket_path = str(tmp_path / "sock")
    conn = UnixHTTPConnection(
        socket_path,
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
        mock_sock.connect.assert_called_with(socket_path)


def test_unix_http_connection_pool_repr(tmp_path: pathlib.Path) -> None:
    """Verify `UnixHTTPConnectionPool` string representation."""
    socket_path = str(tmp_path / "sock")
    pool = UnixHTTPConnectionPool(host=socket_path)
    # Compare lowercased versions to handle Windows path case-insensitivity
    # and urllib3's host normalization.
    assert str(pool).lower() == f"UnixHTTPConnectionPool(host={socket_path})".lower()
