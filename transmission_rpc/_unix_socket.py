# Inspired from:
#   https://github.com/getsentry/sentry/blob/9d03adef66f63e29a5d95189447d02ba0b68c2af/src/sentry/net/http.py#L215-L244
# See also:
#   https://github.com/urllib3/urllib3/issues/1465

from __future__ import annotations

import socket
from typing import Any

from urllib3.connection import HTTPConnection
from urllib3.connectionpool import HTTPConnectionPool


class UnixHTTPConnection(HTTPConnection):
    def __init__(
        self,
        host: str,
        *,
        # The default socket options include `TCP_NODELAY` which won't work here.
        socket_options: None | list[tuple[int, int, int | bytes]] = None,
        **kwargs: Any,
    ):
        self.socket_path = host
        # We're using the `host` as the socket path, but
        # urllib3 uses this host as the Host header by default.
        # If we send along the socket path as a Host header, this is
        # never what you want and would typically be malformed value.
        # So we fake this by sending along `localhost` by default as
        # other libraries do.
        super().__init__(host="localhost", socket_options=socket_options, **kwargs)

    def _new_conn(self) -> socket.socket:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        socket_options = self.socket_options
        if socket_options is not None:
            for lvl, opt, value in socket_options:
                sock.setsockopt(lvl, opt, value)

        if self.timeout is not None:
            sock.settimeout(self.timeout)
        sock.connect(self.socket_path)
        return sock


class UnixHTTPConnectionPool(HTTPConnectionPool):
    ConnectionCls = UnixHTTPConnection  # type: ignore

    def __str__(self) -> str:
        return f"{type(self).__name__}(host={self.host})"
