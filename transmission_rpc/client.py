from __future__ import annotations

import base64
import importlib.metadata
import json
import logging
import os
import pathlib
import string
import time
import types
from collections.abc import Iterable
from typing import Any, BinaryIO, Literal, TypeVar, cast
from urllib.parse import urlparse

import certifi
import urllib3
from typing_extensions import Self, TypedDict
from urllib3 import Timeout
from urllib3.util import make_headers

from transmission_rpc._compat import convert_jsonrpc_args, convert_request_args
from transmission_rpc._tracker_list import serialize_tracker_list
from transmission_rpc._unix_socket import UnixHTTPConnectionPool
from transmission_rpc.constants import LOGGER, RpcMethod, get_torrent_arguments
from transmission_rpc.error import (
    TransmissionAuthError,
    TransmissionConnectError,
    TransmissionError,
    TransmissionTimeoutError,
)
from transmission_rpc.session import Session, SessionStats
from transmission_rpc.torrent import Torrent
from transmission_rpc.types import Group, PortTestResult, get_field

try:
    __version__ = importlib.metadata.version("transmission-rpc")
except ImportError:  # pragma: no cover
    __version__ = "develop"

__USER_AGENT__ = f"transmission-rpc/{__version__} (https://github.com/trim21/transmission-rpc)"

_hex_chars = frozenset(string.hexdigits.lower())

_TorrentID = int | str
_TorrentIDs = _TorrentID | list[_TorrentID] | None

_header_session_id_key = "x-transmission-session-id"

DEFAULT_TIMEOUT = 30.0

# urllib3 may remove support for int/float in the future
_Timeout = Timeout | int | float

_TLS_CERT_FILE_DEFAULT = os.getenv("TRANSMISSION_RPC_PY_CERT_FILE")


class ResponseData(TypedDict, total=False):
    """Transmission RPC response, either JSON-RPC 2.0 or the legacy format."""

    jsonrpc: str
    result: Any
    error: Any
    id: int | str | None
    arguments: Any
    tag: int


class LegacyResponseData(TypedDict):
    arguments: dict[str, Any]
    result: str


def _is_jsonrpc_response(data: Any) -> bool:
    """A response is JSON-RPC 2.0 iff it carries the ``jsonrpc`` field.

    Legacy (pre-4.1.0) servers never emit that field, so its presence is a
    reliable protocol probe. Errors also carry it, so this stays true for
    error responses.
    """
    return isinstance(data, dict) and cast("dict[str, Any]", data).get("jsonrpc") == "2.0"


# RPC methods whose legacy ``download_dir`` argument uses camelCase rather
# than the kebab-case used by the rest of the legacy API.
_TORRENT_METHODS = frozenset(
    {
        RpcMethod.TorrentGet,
        RpcMethod.TorrentSet,
    }
)


def ensure_location_str(s: str | pathlib.Path) -> str:
    if isinstance(s, pathlib.Path):
        if s.is_absolute():
            return str(s)

        raise ValueError(
            "using relative `pathlib.Path` as remote path is not supported in v4.",
        )

    return str(s)


def _parse_torrent_id(raw_torrent_id: Any) -> int | str:
    if isinstance(raw_torrent_id, int):
        if raw_torrent_id >= 0:
            return raw_torrent_id
    elif isinstance(raw_torrent_id, str):
        if len(raw_torrent_id) != 40 or (set(raw_torrent_id) - _hex_chars):
            raise ValueError(f"torrent ids {raw_torrent_id} is not valid torrent id, should be a hex str for sha1 hash")
        return raw_torrent_id
    raise ValueError(f"{raw_torrent_id} is not valid torrent id")


def _parse_torrent_ids(args: Any) -> str | list[str | int]:
    if args is None:
        return []
    if isinstance(args, int):
        return [_parse_torrent_id(args)]
    if isinstance(args, str):
        if args in {"recently-active", "recently_active"}:
            return "recently_active"
        return [_parse_torrent_id(args)]
    if isinstance(args, (list, tuple)):
        return [_parse_torrent_id(item) for item in args]
    raise ValueError(f"Invalid torrent id {args}")


class Client:
    __query_timeout: Timeout | None

    def __init__(
        self,
        *,
        protocol: Literal["http", "https", "http+unix"] = "http",
        username: str | None = None,
        password: str | None = None,
        host: str = "127.0.0.1",
        port: int | None = 9091,
        path: str = "/transmission/rpc",
        timeout: float | Timeout | None = DEFAULT_TIMEOUT,
        logger: logging.Logger = LOGGER,
        tls_cert_file: str | None = _TLS_CERT_FILE_DEFAULT,
    ):
        """

        Parameters:
            protocol:
            username:
            password:
            host:
            port:
            path: rpc request target path, default ``/transmission/rpc``
            timeout:
            logger:
            tls_cert_file:
                Path to a custom CA bundle file (PEM format) to use for SSL verification.
                Defaults to TRANSMISSION_RPC_PY_CERT_FILE env var if set.
                If None, uses certifi's default bundle.

        To connect to a Unix socket, pass "http+unix" as `protocol` and the path to
        the socket as `host`.
        """
        if isinstance(logger, logging.Logger):
            self.logger = logger
        else:
            raise TypeError(
                "logger must be instance of `logging.Logger`, default: logging.getLogger('transmission-rpc')"
            )
        if isinstance(timeout, (int, float)):
            self.__query_timeout = Timeout(timeout)
        elif isinstance(timeout, Timeout) or timeout is None:
            self.__query_timeout = timeout
        else:
            raise TypeError(f"unsupported value {timeout!r}, only Timeout/float/int are supported")

        if username or password:
            self.__auth_headers = make_headers(basic_auth=f"{username}:{password}", user_agent=__USER_AGENT__)
        else:
            self.__auth_headers = make_headers(user_agent=__USER_AGENT__)

        if path == "/transmission/":
            path = "/transmission/rpc"

        self._path = path

        self.__raw_session: dict[str, Any] = {}
        self.__session_id = "0"
        # None = protocol not yet probed; True = JSON-RPC 2.0; False = legacy
        self.__use_jsonrpc: bool | None = None
        self.__request_id = 0

        self.__protocol_version: int = 17  # default 17

        common_args: dict[str, Any] = {"host": host, "timeout": self.timeout, "retries": False}
        if protocol == "http":
            self.__http_client = urllib3.HTTPConnectionPool(port=port, **common_args)
        elif protocol == "https":
            ca_certs = tls_cert_file or certifi.where()
            self.__http_client = urllib3.HTTPSConnectionPool(port=port, ca_certs=ca_certs, **common_args)
        elif protocol == "http+unix":
            self.__http_client = UnixHTTPConnectionPool(**common_args)
        else:
            raise ValueError(f"Unknown protocol {protocol!r}, only 'http', 'https' or 'http+unix' is supported")
        self.get_session(arguments=["rpc_version"])
        self.__torrent_get_arguments = get_torrent_arguments(self.__protocol_version)

    @property
    def timeout(self) -> Timeout | None:
        """
        Get current timeout for HTTP queries.
        """
        return self.__query_timeout

    @timeout.setter
    def timeout(self, value: Timeout) -> None:
        """
        Set timeout for HTTP queries.
        """
        if not isinstance(value, Timeout):
            raise TypeError("must use Timeout instance")

        self.__query_timeout = value

    @timeout.deleter
    def timeout(self) -> None:
        """
        Reset the HTTP query timeout to the default.
        """
        self.__query_timeout = Timeout(DEFAULT_TIMEOUT)

    def __get_headers(self) -> dict[str, str]:
        self.__auth_headers[_header_session_id_key] = self.__session_id

        return self.__auth_headers

    def _http_query(self, query: dict[str, Any], timeout: _Timeout | None = None) -> str:
        """
        Query Transmission through HTTP.
        """
        request_count = 0

        if timeout is None:
            timeout = self.__query_timeout

        while True:
            if request_count >= 3:
                raise TransmissionError("too much request, try enable logger to see what happened")

            headers = self.__get_headers()
            log_headers = headers.copy()
            if "authorization" in log_headers:
                log_headers["authorization"] = "******"
            self.logger.debug({"path": self._path, "headers": log_headers, "data": query, "timeout": timeout})

            request_count += 1
            try:
                r = self.__http_client.request(
                    "POST",
                    url=self._path,
                    headers=headers,
                    json=query,
                    timeout=timeout,
                )
            except urllib3.exceptions.TimeoutError as e:
                raise TransmissionTimeoutError("timeout when connection to transmission daemon") from e
            except urllib3.exceptions.ConnectionError as e:
                raise TransmissionConnectError(f"can't connect to transmission daemon: {e!s}") from e

            self.logger.debug(r.data)
            if r.status in {401, 403}:
                self.logger.debug(headers)
                raise TransmissionAuthError("transmission daemon require auth", original=r)

            if _header_session_id_key in r.headers:
                self.__session_id = r.headers[_header_session_id_key]

            if r.status != 409:
                return r.data.decode("utf-8")

    def _request(
        self,
        method: RpcMethod,
        arguments: dict[str, Any] | None = None,
        ids: _TorrentIDs | None = None,
        require_ids: bool = False,
        timeout: _Timeout | None = None,
    ) -> dict[str, Any]:
        """
        Send an RPC request to Transmission using HTTP POST.

        Uses the JSON-RPC 2.0 protocol when the server supports it (4.1.0+),
        probing on the first request and permanently falling back to the legacy
        bespoke protocol for older servers.
        """
        if not isinstance(method, str):
            raise TypeError("request takes method as string")  # pragma: no cover
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise TypeError("request takes arguments should be dict")  # pragma: no cover

        ids = _parse_torrent_ids(ids)
        if len(ids) > 0:
            arguments["ids"] = ids
        elif require_ids:
            raise ValueError("request require ids")

        query = self._build_query(method, arguments)

        start = time.monotonic()
        try:
            http_data = self._http_query(query, timeout)
        finally:
            elapsed = time.monotonic() - start
            self.logger.debug("http request took %.3f s", elapsed)

        try:
            data: ResponseData = json.loads(http_data)
        except json.JSONDecodeError as error:
            self.logger.exception("Error:")
            self.logger.exception('Request: "%s"', query)
            self.logger.exception('HTTP data: "%s"', http_data)
            raise TransmissionError(
                "failed to parse response as json", method=method, argument=arguments, raw_response=http_data
            ) from error

        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(json.dumps(data, indent=2))

        if self.__use_jsonrpc is None:
            # The first request doubles as the protocol probe. A response
            # without the `jsonrpc` field means a pre-4.1.0 server: fall back
            # to the legacy protocol and resend the request once.
            if _is_jsonrpc_response(data):
                self.__use_jsonrpc = True
            else:
                self.__use_jsonrpc = False
                self.logger.debug("server does not support JSON-RPC 2.0, falling back to legacy protocol")
                start = time.monotonic()
                try:
                    http_data = self._http_query(self._build_query(method, arguments), timeout)
                finally:
                    elapsed = time.monotonic() - start
                    self.logger.debug("legacy retry took %.3f s", elapsed)
                try:
                    data = json.loads(http_data)
                except json.JSONDecodeError as error:
                    self.logger.exception("Error:")
                    self.logger.exception('Request: "%s"', query)
                    self.logger.exception('HTTP data: "%s"', http_data)
                    raise TransmissionError(
                        "failed to parse response as json", method=method, argument=arguments, raw_response=http_data
                    ) from error

        res = self._parse_response(method, data, arguments, http_data)

        if method == RpcMethod.TorrentGet:
            return res
        if method == RpcMethod.TorrentAdd:
            results: dict[str, Any] = {}
            item = get_field(res, "torrent_added", None)
            if item is None:
                item = get_field(res, "torrent_duplicate", None)
            if item:
                results[item["id"]] = Torrent(fields=item)
            else:
                raise TransmissionError(
                    "Invalid torrent-add response.",
                    method=method,
                    argument=arguments,
                    response=data,
                    raw_response=http_data,
                )
            return results
        if method == RpcMethod.SessionGet:
            self.__raw_session.update(res)
        if method == RpcMethod.SessionStats:
            # older versions of T have the return data in "session-stats"
            session_stats = get_field(res, "session_stats", None)
            if session_stats is not None:
                return session_stats
            return res

        return res

    def _build_query(self, method: RpcMethod, arguments: dict[str, Any]) -> dict[str, Any]:
        """Build the request payload in the current protocol format.

        An unprobed client (``__use_jsonrpc is None``) sends JSON-RPC 2.0,
        since that first request doubles as the protocol probe.
        """
        self.__request_id += 1
        if self.__use_jsonrpc is not False:
            return {
                "jsonrpc": "2.0",
                "method": method.value.replace("-", "_"),
                "params": convert_jsonrpc_args(arguments),
                "id": self.__request_id,
            }
        return {
            "method": method.value,
            "arguments": convert_request_args(arguments, torrent=method in _TORRENT_METHODS),
        }

    def _parse_response(
        self,
        method: RpcMethod,
        data: ResponseData,
        arguments: dict[str, Any],
        http_data: str,
    ) -> dict[str, Any]:
        """Extract the result object from a response, raising on errors."""
        if self.__use_jsonrpc:
            if "error" in data:
                error = data["error"]
                error_data = cast("dict[str, Any]", error) if isinstance(error, dict) else {}
                message = error_data.get("message", "unknown error")
                details = error_data.get("data")
                if isinstance(details, dict) and "error_string" in details:
                    message = f"{message}: {details['error_string']}"
                raise TransmissionError(
                    message,
                    method=method,
                    argument=arguments,
                    response=data,
                    raw_response=http_data,
                )
            if "result" not in data:
                raise TransmissionError(
                    "Query failed, response data missing without result.",
                    method=method,
                    argument=arguments,
                    response=data,
                    raw_response=http_data,
                )
            return data["result"]

        if "result" not in data:
            raise TransmissionError(
                "Query failed, response data missing without result.",
                method=method,
                argument=arguments,
                response=data,
                raw_response=http_data,
            )

        legacy_data = cast("LegacyResponseData", data)
        if legacy_data["result"] != "success":
            raise TransmissionError(
                f'Query failed with result "{legacy_data["result"]}".',
                method=method,
                argument=arguments,
                response=data,
                raw_response=http_data,
            )

        return legacy_data["arguments"]

    def _update_rpc_version(self) -> None:
        """Cache the Transmission RPC version used for field selection."""
        self.__protocol_version = get_field(self.__raw_session, "rpc_version")

    def _rpc_version_warning(self, required_version: int) -> None:
        """
        Add a warning to the log if the Transmission RPC version is lower then the provided version.
        """
        if self.__protocol_version < required_version:
            self.logger.warning(
                "Using feature not supported by server. RPC version for server %d, feature introduced in %d.",
                self.__protocol_version,
                required_version,
            )

    def add_torrent(
        self,
        torrent: BinaryIO | str | bytes | pathlib.Path,
        timeout: _Timeout | None = None,
        *,
        download_dir: str | None = None,
        files_unwanted: list[int] | None = None,
        files_wanted: list[int] | None = None,
        paused: bool | None = None,
        peer_limit: int | None = None,
        priority_high: list[int] | None = None,
        priority_low: list[int] | None = None,
        priority_normal: list[int] | None = None,
        cookies: str | None = None,
        labels: Iterable[str] | None = None,
        bandwidth_priority: int | None = None,
        sequential_download: bool | None = None,
        sequential_download_from_piece: int | None = None,
    ) -> Torrent:
        """
        Add torrent to transfers list. ``torrent`` can be:

        - ``http://``, ``https://`` or  ``magnet:`` URL
        - torrent file-like object in **binary mode**
        - bytes of torrent content
        - ``pathlib.Path`` for local torrent file, will be read and encoded as base64.

        Warnings:
            base64 string or ``file://`` protocol URL are not supported in v4.

        Parameters:
            torrent:
                torrent to add
            timeout:
                request timeout
            bandwidth_priority:
                Priority for this transfer.
            cookies:
                One or more HTTP cookie(s).
            download_dir:
                The directory where the downloaded contents will be saved in.
            files_unwanted:
                A list of file id's that shouldn't be downloaded.
            files_wanted:
                A list of file id's that should be downloaded.
            paused:
                If ``True``, does not start the transfer when added.
                Magnet url will always start to downloading torrents.
            peer_limit:
                Maximum number of peers allowed.
            priority_high:
                A list of file id's that should have high priority.
            priority_low:
                A list of file id's that should have low priority.
            priority_normal:
                A list of file id's that should have normal priority.
            labels:
                Array of string labels.
                Add in rpc 17.
            sequential_download:
                download torrent pieces sequentially.
                Add in rpc 18.
            sequential_download_from_piece:
                first piece to download when sequential download is enabled.
                Add in rpc 18.
        """
        if labels is not None:
            self._rpc_version_warning(17)

        if sequential_download is not None or sequential_download_from_piece is not None:
            self._rpc_version_warning(18)

        kwargs: dict[str, Any] = remove_unset_value(
            {
                "download_dir": download_dir,
                "files_unwanted": files_unwanted,
                "files_wanted": files_wanted,
                "paused": paused,
                "peer_limit": peer_limit,
                "priority_high": priority_high,
                "priority_low": priority_low,
                "priority_normal": priority_normal,
                "bandwidth_priority": bandwidth_priority,
                "sequential_download": sequential_download,
                "sequential_download_from_piece": sequential_download_from_piece,
                "cookies": cookies,
                "labels": list_or_none(_single_str_as_list(labels)),
            }
        )

        torrent_data = _try_read_torrent(torrent)
        if torrent_data is None:
            kwargs["filename"] = torrent
        else:
            if not torrent_data:
                raise ValueError("Torrent metadata is empty")
            kwargs["metainfo"] = torrent_data

        return next(iter(self._request(RpcMethod.TorrentAdd, kwargs, timeout=timeout).values()))

    def remove_torrent(self, ids: _TorrentIDs, delete_data: bool = False, timeout: _Timeout | None = None) -> None:
        """
        remove torrent(s) with provided id(s).

        Local data will be removed by transmission daemon if ``delete_data`` is set to ``True``.
        """
        self._request(
            RpcMethod.TorrentRemove,
            {"delete_local_data": delete_data},
            ids,
            True,
            timeout=timeout,
        )

    def start_torrent(self, ids: _TorrentIDs = None, timeout: _Timeout | None = None) -> None:
        """Start torrent(s), or all torrents if ids is empty, respecting the queue order."""
        self._request(RpcMethod.TorrentStart, {}, ids, timeout=timeout)

    def start_torrent_now(self, ids: _TorrentIDs = None, timeout: _Timeout | None = None) -> None:
        """Start torrent(s), or all torrents if ids is empty, bypassing the queue order."""
        self._request(RpcMethod.TorrentStartNow, {}, ids, timeout=timeout)

    def stop_torrent(self, ids: _TorrentIDs, timeout: _Timeout | None = None) -> None:
        """stop torrent(s) with provided id(s)"""
        self._request(RpcMethod.TorrentStop, {}, ids, True, timeout=timeout)

    def verify_torrent(self, ids: _TorrentIDs, timeout: _Timeout | None = None) -> None:
        """verify torrent(s) with provided id(s)"""
        self._request(RpcMethod.TorrentVerify, {}, ids, True, timeout=timeout)

    def reannounce_torrent(self, ids: _TorrentIDs, timeout: _Timeout | None = None) -> None:
        """Reannounce torrent(s) with provided id(s)"""
        self._request(RpcMethod.TorrentReannounce, {}, ids, True, timeout=timeout)

    def get_torrent(
        self,
        torrent_id: _TorrentID,
        arguments: Iterable[str] | None = None,
        timeout: _Timeout | None = None,
    ) -> Torrent:
        """
        Get information for torrent with provided id.
        ``arguments`` contains a list of field names to be returned, when ``arguments=None`` (default),
        all fields are requested. See the Torrent class for more information.

        new argument ``format`` in rpc_version 16 is unnecessarily
        and this lib can't handle table response, So it's unsupported.

        Returns a Torrent object with the requested fields.

        Note:
            It's recommended that you only fetch arguments you need,
            this could improve response speed.

            For example, fetch all fields from transmission daemon with 1500 torrents would take ~5s,
            but is only ~0.2s if to fetch 6 fields.

        Parameters:
            torrent_id:
                torrent id can be an int or a torrent ``info_hash`` (``hash_string`` property of the ``Torrent`` object).

            arguments:
                fetched torrent arguments, in most cases you don't need to set this,
                transmission-rpc will fetch all torrent fields it supported.

            timeout:
                requests timeout

        Raises:
            KeyError: torrent with given ``torrent_id`` not found
        """
        if arguments:
            arguments = list(set(arguments) | {"id", "hash_string"})
        else:
            arguments = self.__torrent_get_arguments
        torrent_id = _parse_torrent_id(torrent_id)

        result = self._request(
            RpcMethod.TorrentGet,
            {"fields": arguments},
            torrent_id,
            require_ids=True,
            timeout=timeout,
        )

        for torrent in result["torrents"]:
            if get_field(torrent, "hash_string", None) == torrent_id or get_field(torrent, "id", None) == torrent_id:
                return Torrent(fields=torrent)
        raise KeyError("Torrent not found in result")

    def get_torrents(
        self,
        ids: _TorrentIDs | None = None,
        arguments: Iterable[str] | None = None,
        timeout: _Timeout | None = None,
    ) -> list[Torrent]:
        """
        Get information for torrents with provided ids. For more information see :py:meth:`Client.get_torrent`.

        Returns a list of Torrent object.
        """
        if arguments:
            arguments = list(set(arguments) | {"id", "hash_string"})
        else:
            arguments = self.__torrent_get_arguments
        return [
            Torrent(fields=x)
            for x in self._request(RpcMethod.TorrentGet, {"fields": arguments}, ids, timeout=timeout)["torrents"]
        ]

    def get_recently_active_torrents(
        self, arguments: Iterable[str] | None = None, timeout: _Timeout | None = None
    ) -> tuple[list[Torrent], list[int]]:
        """
        Get information for torrents for recently active torrent. If you want to get recently-removed
        torrents. you should use this method.

        Returns:
            active_torrents, removed_torrents
                list of recently active torrents and list of torrent-id of recently-removed torrents.
        """
        if arguments:
            arguments = list(set(arguments) | {"id", "hash_string"})
        else:
            arguments = self.__torrent_get_arguments

        result = self._request(RpcMethod.TorrentGet, {"fields": arguments}, "recently_active", timeout=timeout)

        return [Torrent(fields=x) for x in result["torrents"]], result["removed"]

    def change_torrent(
        self,
        ids: _TorrentIDs,
        timeout: _Timeout | None = None,
        *,
        bandwidth_priority: int | None = None,
        download_limit: int | None = None,
        download_limited: bool | None = None,
        upload_limit: int | None = None,
        upload_limited: bool | None = None,
        files_unwanted: Iterable[int] | None = None,
        files_wanted: Iterable[int] | None = None,
        honors_session_limits: bool | None = None,
        location: str | None = None,
        peer_limit: int | None = None,
        priority_high: Iterable[int] | None = None,
        priority_low: Iterable[int] | None = None,
        priority_normal: Iterable[int] | None = None,
        queue_position: int | None = None,
        seed_idle_limit: int | None = None,
        seed_idle_mode: int | None = None,
        seed_ratio_limit: float | None = None,
        seed_ratio_mode: int | None = None,
        labels: Iterable[str] | None = None,
        group: str | None = None,
        tracker_list: Iterable[Iterable[str]] | None = None,
        sequential_download: bool | None = None,
        sequential_download_from_piece: int | None = None,
        tracker_add: Iterable[str] | None = None,
        tracker_replace: Iterable[tuple[int, str]] | None = None,
        tracker_remove: Iterable[int] | None = None,
        **kwargs: Any,
    ) -> None:
        """Change torrent parameters for the torrent(s) with the supplied id's.

        Parameters:
            ids: torrent(s) to change.
            timeout: requesst timeout.
            honors_session_limits: true if session upload limits are honored.
            location: new location of the torrent's content
            peer_limit: maximum number of peers
            queue_position: position of this torrent in its queue [0...n)
            files_wanted: Array of file id to download.
            files_unwanted: Array of file id to not download.
            download_limit: maximum download speed (KBps)
            download_limited: true if ``download_limit`` is honored
            upload_limit: maximum upload speed (KBps)
            upload_limited: true if ``upload_limit`` is honored
            bandwidth_priority: Priority for this transfer.
            priority_high: list of file id to set high download priority
            priority_low: list of file id to set low download priority
            priority_normal: list of file id to set normal download priority
            seed_ratio_limit: Seed inactivity limit in minutes.
            seed_ratio_mode: Torrent seed ratio mode
                Valid options are :py:class:`transmission_rpc.RatioLimitMode`
            seed_idle_limit: torrent-level seeding ratio
            seed_idle_mode: Seed inactivity mode.
                Valid options are :py:class:`transmission_rpc.IdleMode`
            labels: Array of string labels. Add in rpc 16.
            group: The name of this torrent's bandwidth group. Add in rpc 17.

            tracker_list: An ``Iterable[Iterable[str]]`` whose inner iterables are tracker tiers.

                Add in rpc 17.

                Example: ``[['https://tracker1/announce', 'https://tracker2/announce'],
                ['https://backup1.example.com/announce'], ['https://backup2.example.com/announce']]``.

                An empty outer iterable clears the tracker list. Strings are not accepted as tiers, and empty tiers,
                empty tracker URLs, non-string tracker URLs, and tracker URLs containing CR or LF are rejected.

            sequential_download: download torrent pieces sequentially. Add in Transmission 4.1.0, rpc-version 18.
            sequential_download_from_piece: first piece to download in sequential mode. Add in rpc 18.

            tracker_add: Array of string with announce URLs to add.
                **Deprecated** since transmission daemon 4.0.0, this argument is deprecated,
                use ``tracker_list`` instead.

            tracker_remove: Array of ids of trackers to remove.
                **Deprecated** since transmission daemon 4.0.0, this argument is deprecated,
                use ``tracker_list`` instead.

            tracker_replace: Array of (id, url) tuples where the announcement URL should be replaced.
                **Deprecated** since transmission daemon 4.0.0, this argument is deprecated,
                use ``tracker_list`` instead.

        Warnings:
            ``kwargs`` is for the future features not supported yet, it's not compatibility promising.
            Known legacy argument names are normalized for the selected protocol.
        """
        if labels is not None:
            self._rpc_version_warning(16)

        if tracker_list is not None:
            self._rpc_version_warning(17)

        if group is not None:
            self._rpc_version_warning(17)

        if sequential_download is not None or sequential_download_from_piece is not None:
            self._rpc_version_warning(18)

        args: dict[str, Any] = remove_unset_value(
            {
                "bandwidth_priority": bandwidth_priority,
                "download_limit": download_limit,
                "download_limited": download_limited,
                "upload_limit": upload_limit,
                "upload_limited": upload_limited,
                "files_unwanted": list_or_none(files_unwanted),
                "files_wanted": list_or_none(files_wanted),
                "honors_session_limits": honors_session_limits,
                "location": location,
                "peer_limit": peer_limit,
                "priority_high": list_or_none(priority_high),
                "priority_low": list_or_none(priority_low),
                "priority_normal": list_or_none(priority_normal),
                "queue_position": queue_position,
                "seed_idle_limit": seed_idle_limit,
                "seed_idle_mode": seed_idle_mode,
                "seed_ratio_limit": seed_ratio_limit,
                "seed_ratio_mode": seed_ratio_mode,
                "tracker_add": tracker_add,
                "tracker_remove": tracker_remove,
                "tracker_replace": tracker_replace,
                "labels": list_or_none(_single_str_as_list(labels)),
                "tracker_list": None if tracker_list is None else serialize_tracker_list(tracker_list),
                "group": group,
                "sequential_download": sequential_download,
                "sequential_download_from_piece": sequential_download_from_piece,
            }
        )

        args.update(kwargs)

        if args:
            self._request(RpcMethod.TorrentSet, args, ids, True, timeout=timeout)
        else:
            raise ValueError("No arguments to set")

    def move_torrent_data(
        self,
        ids: _TorrentIDs,
        location: str | pathlib.Path,
        timeout: _Timeout | None = None,
        *,
        move: bool = True,
    ) -> None:
        """
        Move torrent data to the new location.

        See Also:
            `RPC Spec: moving-a-torrent
            <https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md#36-moving-a-torrent>`_
        """
        args = {"location": ensure_location_str(location), "move": bool(move)}
        self._request(RpcMethod.TorrentSetLocation, args, ids, True, timeout=timeout)

    def rename_torrent_path(
        self,
        torrent_id: _TorrentID,
        location: str,
        name: str,
        timeout: _Timeout | None = None,
    ) -> tuple[str, str]:
        """
        Warnings:
            This method can only be called on single torrent.

        Warnings:
            This is not the method to move torrent data directory,

        See Also:
            `RPC Spec: renaming-a-torrents-path
            <https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md#37-renaming-a-torrents-path>`_
        """
        self._rpc_version_warning(15)
        torrent_id = _parse_torrent_id(torrent_id)

        name = name.strip()  # https://github.com/trim21/transmission-rpc/issues/185

        result = self._request(
            RpcMethod.TorrentRenamePath,
            {"path": ensure_location_str(location), "name": name},
            torrent_id,
            True,
            timeout=timeout,
        )

        return result["path"], result["name"]

    def queue_top(self, ids: _TorrentIDs, timeout: _Timeout | None = None) -> None:
        """
        Move transfer to the top of the queue.

        https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md#46-queue-movement-requests
        """
        self._request(RpcMethod.QueueMoveTop, ids=ids, require_ids=True, timeout=timeout)

    def queue_bottom(self, ids: _TorrentIDs, timeout: _Timeout | None = None) -> None:
        """
        Move transfer to the bottom of the queue.

        https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md#46-queue-movement-requests
        """
        self._request(RpcMethod.QueueMoveBottom, ids=ids, require_ids=True, timeout=timeout)

    def queue_up(self, ids: _TorrentIDs, timeout: _Timeout | None = None) -> None:
        """Move transfer up in the queue."""
        self._request(RpcMethod.QueueMoveUp, ids=ids, require_ids=True, timeout=timeout)

    def queue_down(self, ids: _TorrentIDs, timeout: _Timeout | None = None) -> None:
        """Move transfer down in the queue."""
        self._request(RpcMethod.QueueMoveDown, ids=ids, require_ids=True, timeout=timeout)

    def get_session(
        self,
        timeout: _Timeout | None = None,
        arguments: Iterable[str] | None = None,
    ) -> Session:
        """
        Get session parameters. See the Session class for more information.
        """

        data: dict[str, Any] = {}
        if arguments:
            data["fields"] = list(arguments)

        self._request(RpcMethod.SessionGet, timeout=timeout, arguments=data)
        self._update_rpc_version()
        return Session(fields=self.__raw_session)

    def set_session(
        self,
        timeout: _Timeout | None = None,
        *,
        alt_speed_down: int | None = None,
        alt_speed_enabled: bool | None = None,
        alt_speed_time_begin: int | None = None,
        alt_speed_time_day: int | None = None,
        alt_speed_time_enabled: bool | None = None,
        alt_speed_time_end: int | None = None,
        alt_speed_up: int | None = None,
        anti_brute_force_enabled: bool | None = None,
        blocklist_enabled: bool | None = None,
        blocklist_url: str | None = None,
        cache_size_mib: int | None = None,
        dht_enabled: bool | None = None,
        default_trackers: Iterable[str] | None = None,
        download_dir: str | None = None,
        download_queue_enabled: bool | None = None,
        download_queue_size: int | None = None,
        encryption: Literal["required", "preferred", "allowed", "tolerated"] | None = None,
        idle_seeding_limit: int | None = None,
        idle_seeding_limit_enabled: bool | None = None,
        incomplete_dir: str | None = None,
        incomplete_dir_enabled: bool | None = None,
        lpd_enabled: bool | None = None,
        peer_limit_global: int | None = None,
        peer_limit_per_torrent: int | None = None,
        peer_port: int | None = None,
        peer_port_random_on_start: bool | None = None,
        pex_enabled: bool | None = None,
        port_forwarding_enabled: bool | None = None,
        preferred_transports: Iterable[Literal["utp", "tcp"]] | None = None,
        queue_stalled_enabled: bool | None = None,
        queue_stalled_minutes: int | None = None,
        rename_partial_files: bool | None = None,
        reqq: int | None = None,
        script_torrent_done_enabled: bool | None = None,
        script_torrent_done_filename: str | None = None,
        seed_queue_enabled: bool | None = None,
        seed_queue_size: int | None = None,
        seed_ratio_limit: float | None = None,
        seed_ratio_limited: bool | None = None,
        sequential_download: bool | None = None,
        speed_limit_down: int | None = None,
        speed_limit_down_enabled: bool | None = None,
        speed_limit_up: int | None = None,
        speed_limit_up_enabled: bool | None = None,
        start_added_torrents: bool | None = None,
        trash_original_torrent_files: bool | None = None,
        utp_enabled: bool | None = None,
        script_torrent_done_seeding_filename: str | None = None,
        script_torrent_done_seeding_enabled: bool | None = None,
        script_torrent_added_enabled: bool | None = None,
        script_torrent_added_filename: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Set session parameters.

        Parameters:
            timeout
                request timeout
            alt_speed_down:
                max global download speed (KBps)
            alt_speed_enabled:
                true means use the alt speeds
            alt_speed_time_begin:
                Time when alternate speeds should be enabled. Minutes after midnight.
            alt_speed_time_day:
                Enables alternate speeds scheduling these days.
            alt_speed_time_enabled:
                Enables alternate speeds scheduling.
            alt_speed_time_end:
                Time when alternate speeds should be disabled. Minutes after midnight.
            alt_speed_up:
                Alternate session upload speed limit (in Kib/s).
            blocklist_enabled:
                Enables the block list
            blocklist_url:
                Location of the block list. Updated with blocklist-update.
            cache_size_mib:
                The maximum size of the disk cache in MB
            default_trackers:
                list of default trackers to use on public torrents.
            dht_enabled:
                Enables DHT.
            download_dir:
                Set the session download directory.
            download_queue_enabled:
                Enables download queue.
            download_queue_size:
                Number of slots in the download queue.
            encryption:
                Set the session encryption mode. JSON-RPC 2.0 uses ``allowed``;
                the legacy spelling ``tolerated`` is accepted for compatibility.
            idle_seeding_limit:
                The default seed inactivity limit in minutes.
            idle_seeding_limit_enabled:
                Enables the default seed inactivity limit
            incomplete_dir:
                The path to the directory of incomplete transfer data.
            incomplete_dir_enabled:
                Enables the incomplete transfer data directory,
                Otherwise data for incomplete transfers are stored in the download target.
            lpd_enabled:
                Enables local peer discovery for public torrents.
            peer_limit_global:
                Maximum number of peers.
            peer_limit_per_torrent:
                Maximum number of peers per transfer.
            peer_port:
                Peer port.
            peer_port_random_on_start:
                Enables randomized peer port on start of Transmission.
            pex_enabled:
                Allowing PEX in public torrents.
            port_forwarding_enabled:
                Enables port forwarding.
            queue_stalled_enabled:
                Enable tracking of stalled transfers.
            queue_stalled_minutes:
                Number of minutes of idle that marks a transfer as stalled.
            rename_partial_files:
                Appends ".part" to incomplete files

            seed_queue_enabled:
                Enables upload queue.
            seed_queue_size:
                Number of slots in the upload queue.
            seed_ratio_limit:
                Seed ratio limit. 1.0 means 1:1 download and upload ratio.
            seed_ratio_limited:
                Enables seed ration limit.
            speed_limit_down:
                Download speed limit (in Kib/s).
            speed_limit_down_enabled:
                Enables download speed limiting.
            speed_limit_up:
                Upload speed limit (in Kib/s).
            speed_limit_up_enabled:
                Enables upload speed limiting.
            start_added_torrents:
                Added torrents will be started right away.
            trash_original_torrent_files:
                The .torrent file of added torrents will be deleted.
            utp_enabled:
                Enables Micro Transport Protocol (UTP).
            script_torrent_done_enabled:
                Whether to call the "done" script.
            script_torrent_done_filename:
                Filename of the script to run when the transfer is done.
            script_torrent_added_filename:
                filename of the script to run
            script_torrent_added_enabled:
                whether or not to call the ``added`` script
            script_torrent_done_seeding_enabled:
                whether or not to call the ``seeding-done`` script
            script_torrent_done_seeding_filename:
                filename of the script to run

        Warnings:
            ``kwargs`` is pass the arguments not supported yet future, it's not compatibility promising.
            Known legacy argument names are normalized for the selected protocol.
        """

        if encryption is not None and encryption not in ["required", "preferred", "allowed", "tolerated"]:
            raise ValueError("Invalid encryption value")

        if default_trackers is not None:
            self._rpc_version_warning(17)
        if script_torrent_done_seeding_filename is not None:
            self._rpc_version_warning(17)
        if script_torrent_done_seeding_enabled is not None:
            self._rpc_version_warning(17)
        if script_torrent_added_enabled is not None:
            self._rpc_version_warning(17)
        if script_torrent_added_filename is not None:
            self._rpc_version_warning(17)
        if preferred_transports is not None or sequential_download is not None:
            self._rpc_version_warning(18)

        args: dict[str, Any] = remove_unset_value(
            {
                "alt_speed_down": alt_speed_down,
                "alt_speed_enabled": alt_speed_enabled,
                "alt_speed_time_begin": alt_speed_time_begin,
                "alt_speed_time_day": alt_speed_time_day,
                "alt_speed_time_enabled": alt_speed_time_enabled,
                "alt_speed_time_end": alt_speed_time_end,
                "alt_speed_up": alt_speed_up,
                "anti_brute_force_enabled": anti_brute_force_enabled,
                "blocklist_enabled": blocklist_enabled,
                "blocklist_url": blocklist_url,
                "cache_size_mib": cache_size_mib,
                "dht_enabled": dht_enabled,
                "download_dir": download_dir,
                "download_queue_enabled": download_queue_enabled,
                "download_queue_size": download_queue_size,
                "idle_seeding_limit_enabled": idle_seeding_limit_enabled,
                "idle_seeding_limit": idle_seeding_limit,
                "incomplete_dir": incomplete_dir,
                "incomplete_dir_enabled": incomplete_dir_enabled,
                "lpd_enabled": lpd_enabled,
                "peer_limit_global": peer_limit_global,
                "peer_limit_per_torrent": peer_limit_per_torrent,
                "peer_port_random_on_start": peer_port_random_on_start,
                "peer_port": peer_port,
                "pex_enabled": pex_enabled,
                "port_forwarding_enabled": port_forwarding_enabled,
                "preferred_transports": list_or_none(preferred_transports),
                "queue_stalled_enabled": queue_stalled_enabled,
                "queue_stalled_minutes": queue_stalled_minutes,
                "rename_partial_files": rename_partial_files,
                "reqq": reqq,
                "script_torrent_done_enabled": script_torrent_done_enabled,
                "script_torrent_done_filename": script_torrent_done_filename,
                "seed_queue_enabled": seed_queue_enabled,
                "seed_queue_size": seed_queue_size,
                "seed_ratio_limit": seed_ratio_limit,
                "seed_ratio_limited": seed_ratio_limited,
                "sequential_download": sequential_download,
                "speed_limit_down": speed_limit_down,
                "speed_limit_down_enabled": speed_limit_down_enabled,
                "speed_limit_up": speed_limit_up,
                "speed_limit_up_enabled": speed_limit_up_enabled,
                "start_added_torrents": start_added_torrents,
                "trash_original_torrent_files": trash_original_torrent_files,
                "utp_enabled": utp_enabled,
                "encryption": encryption,
                "script_torrent_added_filename": script_torrent_added_filename,
                "script_torrent_done_seeding_filename": script_torrent_done_seeding_filename,
                "script_torrent_done_seeding_enabled": script_torrent_done_seeding_enabled,
                "script_torrent_added_enabled": script_torrent_added_enabled,
                "default_trackers": "\n".join(default_trackers) if default_trackers is not None else None,
            }
        )

        args.update(kwargs)

        if args:
            self._request(RpcMethod.SessionSet, args, timeout=timeout)

    def blocklist_update(self, timeout: _Timeout | None = None) -> int | None:
        """Update block list. Returns the size of the block list."""
        result = self._request(RpcMethod.BlocklistUpdate, timeout=timeout)
        return get_field(result, "blocklist_size", None)

    def port_test(
        self, timeout: _Timeout | None = None, *, ip_protocol: Literal["ipv4", "ipv6"] | None = None
    ) -> PortTestResult:
        """
        Tests to see if your incoming peer port is accessible from the
        outside world.

        https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md#44-port-checking

        Parameters:
            ip_protocol: ``ipv4`` or ``ipv6``.
                Available in Transmission 4.1.0 (rpc-version-semver 6.0.0, rpc-version: 18)
            timeout: request timeout
        """
        return PortTestResult(
            fields=self._request(RpcMethod.PortTest, remove_unset_value({"ip_protocol": ip_protocol}), timeout=timeout)
        )

    def free_space(self, path: str | pathlib.Path, timeout: _Timeout | None = None) -> int | None:
        """
        Get the amount of free space (in bytes) at the provided location.
        """
        self._rpc_version_warning(15)
        path = ensure_location_str(path)
        result: dict[str, Any] = self._request(RpcMethod.FreeSpace, {"path": path}, timeout=timeout)
        if get_field(result, "path") == path:
            return get_field(result, "size_bytes")
        return None

    def session_stats(self, timeout: _Timeout | None = None) -> SessionStats:
        """Get session statistics"""
        result = self._request(RpcMethod.SessionStats, timeout=timeout)
        return SessionStats(fields=result)

    def session_close(self, timeout: _Timeout | None = None) -> None:
        """
        This method tells the transmission session to shut down.

        Warning:
            This method only sends a session-close RPC request.
            It does not manage or enforce session state on the client side.
            Developers are responsible for tracking session state and avoiding
            further requests after the session is closed.
        """
        self._request(RpcMethod.SessionClose, timeout=timeout)

    def set_group(
        self,
        name: str,
        *,
        timeout: _Timeout | None = None,
        honors_session_limits: bool | None = None,
        speed_limit_down_enabled: bool | None = None,
        speed_limit_down: int | None = None,
        speed_limit_up_enabled: bool | None = None,
        speed_limit_up: int | None = None,
    ) -> None:
        """create or update a Bandwidth group.

        :param name: Bandwidth group name
        :param honors_session_limits: true if session upload limits are honored
        :param speed_limit_down_enabled: true means enabled
        :param speed_limit_down: 	max global download speed (KBps)
        :param speed_limit_up_enabled: 	true means enabled
        :param speed_limit_up: max global upload speed (KBps)
        :param timeout: request timeout
        """

        self._rpc_version_warning(17)
        arguments: dict[str, Any] = remove_unset_value(
            {
                "name": name,
                "honors_session_limits": honors_session_limits,
                "speed_limit_down": speed_limit_down,
                "speed_limit_up_enabled": speed_limit_up_enabled,
                "speed_limit_up": speed_limit_up,
                "speed_limit_down_enabled": speed_limit_down_enabled,
            }
        )

        self._request(RpcMethod.GroupSet, arguments, timeout=timeout)

    def get_group(self, name: str, *, timeout: _Timeout | None = None) -> Group | None:
        self._rpc_version_warning(17)
        result: dict[str, Any] = self._request(RpcMethod.GroupGet, {"group": name}, timeout=timeout)

        if result["group"]:
            return Group(fields=result["group"][0])

        return None

    def get_groups(self, name: list[str] | None = None, *, timeout: _Timeout | None = None) -> dict[str, Group]:
        payload = {}
        if name is not None:
            payload = {"group": name}

        result: dict[str, Any] = self._request(RpcMethod.GroupGet, payload, timeout=timeout)

        return {x["name"]: Group(fields=x) for x in result["group"]}

    def close(self) -> None:
        self.__http_client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        self.close()


T = TypeVar("T")


def _single_str_as_list(v: Iterable[str] | None) -> list[str] | None:
    if v is None:
        return v
    if isinstance(v, str):
        return [v]
    return list(v)


def list_or_none(v: Iterable[T] | None) -> list[T] | None:
    if v is None:
        return None
    return list(v)


def remove_unset_value(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


def _try_read_torrent(torrent: BinaryIO | str | bytes | pathlib.Path) -> str | None:
    """
    if torrent should be encoded with base64, return a non-None value.
    """
    # torrent is a str, may be a url
    if isinstance(torrent, str):
        parsed_uri = urlparse(torrent)
        # torrent starts with file, read from local disk and encode it to base64 url.
        if parsed_uri.scheme in ["https", "http", "magnet"]:
            return None

        if parsed_uri.scheme in ["file"]:
            raise ValueError("support for `file://` URL has been removed.")
    elif isinstance(torrent, pathlib.Path):
        return base64.b64encode(torrent.read_bytes()).decode("utf-8")
    elif isinstance(torrent, bytes):
        return base64.b64encode(torrent).decode("utf-8")
    # maybe a file, try read content and encode it.
    elif hasattr(torrent, "read"):
        return base64.b64encode(torrent.read()).decode("utf-8")

    return None
