from __future__ import annotations

import json
import logging
import pathlib
import string
import time
import types
from typing import Any, BinaryIO, Iterable, List, TypeVar, Union
from urllib.parse import quote

import requests
import requests.auth
import requests.exceptions
from typing_extensions import Literal, Self, TypedDict, deprecated

from transmission_rpc.constants import DEFAULT_TIMEOUT, LOGGER, RpcMethod
from transmission_rpc.error import (
    TransmissionAuthError,
    TransmissionConnectError,
    TransmissionError,
    TransmissionTimeoutError,
)
from transmission_rpc.session import Session, SessionStats
from transmission_rpc.torrent import Torrent
from transmission_rpc.types import Group, _Timeout
from transmission_rpc.utils import _try_read_torrent, get_torrent_arguments

_hex_chars = frozenset(string.hexdigits.lower())

_TorrentID = Union[int, str]
_TorrentIDs = Union[_TorrentID, List[_TorrentID], None]

_header_session_id = "x-transmission-session-id"


class ResponseData(TypedDict):
    arguments: Any
    tag: int
    result: str


def ensure_location_str(s: str | pathlib.Path) -> str:
    if isinstance(s, pathlib.Path):
        if s.is_absolute():
            return str(s)

        raise ValueError(
            "using relative `pathlib.Path` as remote path is not supported in v4.",
        )

    return str(s)


def _parse_torrent_id(raw_torrent_id: int | str) -> int | str:
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
        if args == "recently-active":
            return args
        return [_parse_torrent_id(args)]
    if isinstance(args, (list, tuple)):
        return [_parse_torrent_id(item) for item in args]
    raise ValueError(f"Invalid torrent id {args}")


class Client:
    def __init__(
        self,
        *,
        protocol: Literal["http", "https"] = "http",
        username: str | None = None,
        password: str | None = None,
        host: str = "127.0.0.1",
        port: int = 9091,
        path: str = "/transmission/rpc",
        timeout: float = DEFAULT_TIMEOUT,
        logger: logging.Logger = LOGGER,
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
        """
        if isinstance(logger, logging.Logger):
            self.logger = logger
        else:
            raise TypeError(
                "logger must be instance of `logging.Logger`, default: logging.getLogger('transmission-rpc')"
            )
        self._query_timeout: _Timeout = timeout

        username = quote(username or "", safe="$-_.+!*'(),;&=", encoding="utf8") if username else ""
        password = ":" + quote(password or "", safe="$-_.+!*'(),;&=", encoding="utf8") if password else ""
        auth = f"{username}{password}@" if (username or password) else ""

        if path == "/transmission/":
            path = "/transmission/rpc"

        url = f"{protocol}://{auth}{host}:{port}{path}"
        self._url = str(url)
        self.__raw_session: dict[str, Any] = {}
        self.__session_id = "0"
        self.__server_version: str = "(unknown)"
        self.__protocol_version: int = 17  # default 17
        self._http_session = requests.Session()
        self._http_session.trust_env = False
        self.__semver_version = None
        self.get_session()
        self.__torrent_get_arguments = get_torrent_arguments(self.__protocol_version)

    @property
    @deprecated("do not use internal property")
    def url(self) -> str:
        return self._url

    @property
    @deprecated("do not use internal property, use `get_torrent_arguments(rpc_version)` if you need")
    def torrent_get_arguments(self) -> list[str]:
        return self.__torrent_get_arguments

    @property
    @deprecated("do not use internal property, use `.get_session()` instead")
    def raw_session(self) -> dict[str, Any]:
        return self.__raw_session

    @property
    @deprecated("do not use internal property")
    def session_id(self) -> str:
        return self.__session_id

    @property
    @deprecated("do not use internal property, use `.get_session().version` instead")
    def server_version(self) -> str:
        return self.__server_version

    @property
    def timeout(self) -> _Timeout:
        """
        Get current timeout for HTTP queries.
        """
        return self._query_timeout

    @timeout.setter
    def timeout(self, value: _Timeout) -> None:
        """
        Set timeout for HTTP queries.
        """
        if isinstance(value, (tuple, list)):
            if len(value) != 2:
                raise ValueError("timeout tuple can only include 2 numbers elements")
            for v in value:
                if not isinstance(v, (float, int)):
                    raise TypeError("element of timeout tuple can only be int of float")
            self._query_timeout = (value[0], value[1])  # for type checker
        elif value is None:
            self._query_timeout = DEFAULT_TIMEOUT
        else:
            self._query_timeout = float(value)

    @timeout.deleter
    def timeout(self) -> None:
        """
        Reset the HTTP query timeout to the default.
        """
        self._query_timeout = DEFAULT_TIMEOUT

    @property
    def _http_header(self) -> dict[str, str]:
        return {_header_session_id: self.__session_id}

    def _http_query(self, query: dict[str, Any], timeout: _Timeout | None = None) -> str:
        """
        Query Transmission through HTTP.
        """
        request_count = 0
        if timeout is None:
            timeout = self.timeout
        while True:
            if request_count >= 3:
                raise TransmissionError("too much request, try enable logger to see what happened")
            self.logger.debug(
                {
                    "url": self._url,
                    "headers": self._http_header,
                    "data": query,
                    "timeout": timeout,
                }
            )

            request_count += 1
            try:
                r = self._http_session.post(
                    self._url,
                    headers=self._http_header,
                    json=query,
                    timeout=timeout,
                )
            except requests.exceptions.Timeout as e:
                raise TransmissionTimeoutError("timeout when connection to transmission daemon") from e
            except requests.exceptions.ConnectionError as e:
                raise TransmissionConnectError(f"can't connect to transmission daemon: {e!s}") from e

            self.logger.debug(r.text)
            if r.status_code in {401, 403}:
                self.logger.debug(r.request.headers)
                raise TransmissionAuthError("transmission daemon require auth", original=r)

            if _header_session_id in r.headers:
                self.__session_id = r.headers["x-transmission-session-id"]

            if r.status_code != 409:
                return r.text

    def _request(
        self,
        method: RpcMethod,
        arguments: dict[str, Any] | None = None,
        ids: _TorrentIDs | None = None,
        require_ids: bool = False,
        timeout: _Timeout | None = None,
    ) -> dict[str, Any]:
        """
        Send json-rpc request to Transmission using http POST
        """
        if not isinstance(method, str):
            raise TypeError("request takes method as string")
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise TypeError("request takes arguments should be dict")

        ids = _parse_torrent_ids(ids)
        if len(ids) > 0:
            arguments["ids"] = ids
        elif require_ids:
            raise ValueError("request require ids")

        query = {"method": method, "arguments": arguments}

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
                "failed to parse response as json", method=method, argument=arguments, rawResponse=http_data
            ) from error

        self.logger.debug(json.dumps(data, indent=2))
        if "result" not in data:
            raise TransmissionError(
                "Query failed, response data missing without result.",
                method=method,
                argument=arguments,
                response=data,
                rawResponse=http_data,
            )

        if data["result"] != "success":
            raise TransmissionError(
                f'Query failed with result "{data["result"]}".',
                method=method,
                argument=arguments,
                response=data,
                rawResponse=http_data,
            )

        res = data["arguments"]

        results = {}
        if method == RpcMethod.TorrentGet:
            return res
        if method == RpcMethod.TorrentAdd:
            item = None
            if "torrent-added" in res:
                item = res["torrent-added"]
            elif "torrent-duplicate" in res:
                item = res["torrent-duplicate"]
            if item:
                results[item["id"]] = Torrent(fields=item)
            else:
                raise TransmissionError(
                    "Invalid torrent-add response.",
                    method=method,
                    argument=arguments,
                    response=data,
                    rawResponse=http_data,
                )
        elif method == RpcMethod.SessionGet:
            self.__raw_session.update(res)
        elif method == RpcMethod.SessionStats:
            # older versions of T has the return data in "session-stats"
            if "session-stats" in res:
                return res["session-stats"]
            return res
        elif method in (
            RpcMethod.PortTest,
            RpcMethod.BlocklistUpdate,
            RpcMethod.FreeSpace,
            RpcMethod.TorrentRenamePath,
        ):
            return res
        else:
            return res

        return results

    def _update_server_version(self) -> None:
        """Decode the Transmission version string, if available."""
        self.__semver_version = self.__raw_session.get("rpc-version-semver")
        self.__server_version = self.__raw_session["version"]
        self.__protocol_version = self.__raw_session["rpc-version"]

    @property
    @deprecated("use .get_session().rpc_version_semver instead")
    def semver_version(self) -> str | None:
        """Get the Transmission daemon RPC version.

        .. deprecated:: 7.0.5
            Use ``.get_session().rpc_version_semver`` instead
        """
        return self.__semver_version

    @property
    @deprecated("use .get_session().rpc_version instead")
    def rpc_version(self) -> int:
        """Get the Transmission daemon RPC version.

        .. deprecated:: 7.0.5
            Use ``.get_session().rpc_version`` instead
        """
        return self.__protocol_version

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
        bandwidthPriority: int | None = None,
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
            bandwidthPriority:
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
        """
        if torrent is None:
            raise ValueError("add_torrent requires data or a URI.")

        if labels is not None:
            self._rpc_version_warning(17)

        kwargs: dict[str, Any] = remove_unset_value(
            {
                "download-dir": download_dir,
                "files-unwanted": files_unwanted,
                "files-wanted": files_wanted,
                "paused": paused,
                "peer-limit": peer_limit,
                "priority-high": priority_high,
                "priority-low": priority_low,
                "priority-normal": priority_normal,
                "bandwidthPriority": bandwidthPriority,
                "cookies": cookies,
                "labels": list_or_none(_single_str_as_list(labels)),
            }
        )

        torrent_data = _try_read_torrent(torrent)
        if torrent_data:
            kwargs["metainfo"] = torrent_data
        else:
            kwargs["filename"] = torrent

        return next(iter(self._request(RpcMethod.TorrentAdd, kwargs, timeout=timeout).values()))

    def remove_torrent(self, ids: _TorrentIDs, delete_data: bool = False, timeout: _Timeout | None = None) -> None:
        """
        remove torrent(s) with provided id(s).

        Local data will be removed by transmission daemon if ``delete_data`` is set to ``True``.
        """
        self._request(
            RpcMethod.TorrentRemove,
            {"delete-local-data": delete_data},
            ids,
            True,
            timeout=timeout,
        )

    def start_torrent(self, ids: _TorrentIDs, bypass_queue: bool = False, timeout: _Timeout | None = None) -> None:
        """Start torrent(s) with provided id(s)"""
        method = RpcMethod.TorrentStart
        if bypass_queue:
            method = RpcMethod.TorrentStartNow
        self._request(method, {}, ids, True, timeout=timeout)

    def start_all(self, bypass_queue: bool = False, timeout: _Timeout | None = None) -> None:
        """Start all torrents respecting the queue order"""
        method = RpcMethod.TorrentStart
        if bypass_queue:
            method = RpcMethod.TorrentStartNow
        torrent_list = sorted(self.get_torrents(), key=lambda t: t.queue_position)
        self._request(
            method,
            {},
            ids=[x.id for x in torrent_list],
            require_ids=True,
            timeout=timeout,
        )

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
                torrent id can be an int or a torrent ``info_hash`` (``hashString`` property of the ``Torrent`` object).

            arguments:
                fetched torrent arguments, in most cases you don't need to set this,
                transmission-rpc will fetch all torrent fields it supported.

            timeout:
                requests timeout

        Raises:
            KeyError: torrent with given ``torrent_id`` not found
        """
        if arguments:
            arguments = list(set(arguments) | {"id", "hashString"})
        else:
            arguments = self.__torrent_get_arguments
        torrent_id = _parse_torrent_id(torrent_id)
        if torrent_id is None:
            raise ValueError("Invalid id")

        result = self._request(
            RpcMethod.TorrentGet,
            {"fields": arguments},
            torrent_id,
            require_ids=True,
            timeout=timeout,
        )

        for torrent in result["torrents"]:
            if torrent.get("hashString") == torrent_id or torrent.get("id") == torrent_id:
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
            arguments = list(set(arguments) | {"id", "hashString"})
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
            arguments = list(set(arguments) | {"id", "hashString"})
        else:
            arguments = self.__torrent_get_arguments

        result = self._request(RpcMethod.TorrentGet, {"fields": arguments}, "recently-active", timeout=timeout)

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
        tracker_add: Iterable[str] | None = None,
        labels: Iterable[str] | None = None,
        group: str | None = None,
        tracker_list: Iterable[Iterable[str]] | None = None,
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
            tracker_list:
                A ``Iterable[Iterable[str]]``, each ``Iterable[str]`` for a tracker tier.

                Add in rpc 17.

                Example: ``[['https://tracker1/announce', 'https://tracker2/announce'],
                ['https://backup1.example.com/announce'], ['https://backup2.example.com/announce']]``.

            tracker_add:
                Array of string with announce URLs to add.

                Warnings:
                    since transmission daemon 4.0.0, this argument is deprecated, use ``tracker_list`` instead.

            tracker_remove:
                Array of ids of trackers to remove.

                Warnings:
                    since transmission daemon 4.0.0, this argument is deprecated, use ``tracker_list`` instead.

            tracker_replace:
                Array of (id, url) tuples where the announcement URL should be replaced.

                Warning:
                    since transmission daemon 4.0.0, this argument is deprecated, use ``tracker_list`` instead.

        Warnings:
            ``kwargs`` is for the future features not supported yet, it's not compatibility promising.
            It will be bypassed to request arguments **as-is**, the underline in the key will not be replaced, so you should use kwargs like ``{'a-argument': 'value'}``
        """
        if labels is not None:
            self._rpc_version_warning(16)

        if tracker_list is not None:
            self._rpc_version_warning(17)

        if group is not None:
            self._rpc_version_warning(17)

        args: dict[str, Any] = remove_unset_value(
            {
                "bandwidthPriority": bandwidth_priority,
                "downloadLimit": download_limit,
                "downloadLimited": download_limited,
                "uploadLimit": upload_limit,
                "uploadLimited": upload_limited,
                "files-unwanted": list_or_none(files_unwanted),
                "files-wanted": list_or_none(files_wanted),
                "honorsSessionLimits": honors_session_limits,
                "location": location,
                "peer-limit": peer_limit,
                "priority-high": list_or_none(priority_high),
                "priority-low": list_or_none(priority_low),
                "priority-normal": list_or_none(priority_normal),
                "queuePosition": queue_position,
                "seedIdleLimit": seed_idle_limit,
                "seedIdleMode": seed_idle_mode,
                "seedRatioLimit": seed_ratio_limit,
                "seedRatioMode": seed_ratio_mode,
                "trackerAdd": tracker_add,
                "trackerRemove": tracker_remove,
                "trackerReplace": tracker_replace,
                "labels": list_or_none(_single_str_as_list(labels)),
                "trackerList": None if tracker_list is None else "\n\n".join("\n".join(tier) for tier in tracker_list),
                "group": group,
            }
        )

        args.update(kwargs)

        if args:
            self._request(RpcMethod.TorrentSet, args, ids, True, timeout=timeout)
        else:
            ValueError("No arguments to set")

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
            `RPC Spec: moving-a-torrent <https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md#36-moving-a-torrent>`_
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
            `RPC Spec: renaming-a-torrents-path <https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md#37-renaming-a-torrents-path>`_
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

    def get_session(self, timeout: _Timeout | None = None) -> Session:
        """
        Get session parameters. See the Session class for more information.
        """
        self._request(RpcMethod.SessionGet, timeout=timeout)
        self._update_server_version()
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
        blocklist_enabled: bool | None = None,
        blocklist_url: str | None = None,
        cache_size_mb: int | None = None,
        dht_enabled: bool | None = None,
        default_trackers: Iterable[str] | None = None,
        download_dir: str | None = None,
        download_queue_enabled: bool | None = None,
        download_queue_size: int | None = None,
        encryption: Literal["required", "preferred", "tolerated"] | None = None,
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
        queue_stalled_enabled: bool | None = None,
        queue_stalled_minutes: int | None = None,
        rename_partial_files: bool | None = None,
        script_torrent_done_enabled: bool | None = None,
        script_torrent_done_filename: str | None = None,
        seed_queue_enabled: bool | None = None,
        seed_queue_size: int | None = None,
        seed_ratio_limit: int | None = None,
        seed_ratio_limited: bool | None = None,
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
            cache_size_mb:
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
                Set the session encryption mode, one of ``required``, ``preferred`` or ``tolerated``.
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
            transmission-rpc will merge ``kwargs`` in rpc arguments **as-is**
        """

        if encryption is not None and encryption not in ["required", "preferred", "tolerated"]:
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

        args: dict[str, Any] = remove_unset_value(
            {
                "alt-speed-down": alt_speed_down,
                "alt-speed-enabled": alt_speed_enabled,
                "alt-speed-time-begin": alt_speed_time_begin,
                "alt-speed-time-day": alt_speed_time_day,
                "alt-speed-time-enabled": alt_speed_time_enabled,
                "alt-speed-time-end": alt_speed_time_end,
                "alt-speed-up": alt_speed_up,
                "blocklist-enabled": blocklist_enabled,
                "blocklist-url": blocklist_url,
                "cache-size-mb": cache_size_mb,
                "dht-enabled": dht_enabled,
                "download-dir": download_dir,
                "download-queue-enabled": download_queue_enabled,
                "download-queue-size": download_queue_size,
                "idle-seeding-limit-enabled": idle_seeding_limit_enabled,
                "idle-seeding-limit": idle_seeding_limit,
                "incomplete-dir": incomplete_dir,
                "incomplete-dir-enabled": incomplete_dir_enabled,
                "lpd-enabled": lpd_enabled,
                "peer-limit-global": peer_limit_global,
                "peer-limit-per-torrent": peer_limit_per_torrent,
                "peer-port-random-on-start": peer_port_random_on_start,
                "peer-port": peer_port,
                "pex-enabled": pex_enabled,
                "port-forwarding-enabled": port_forwarding_enabled,
                "queue-stalled-enabled": queue_stalled_enabled,
                "queue-stalled-minutes": queue_stalled_minutes,
                "rename-partial-files": rename_partial_files,
                "script-torrent-done-enabled": script_torrent_done_enabled,
                "script-torrent-done-filename": script_torrent_done_filename,
                "seed-queue-enabled": seed_queue_enabled,
                "seed-queue-size": seed_queue_size,
                "seedRatioLimit": seed_ratio_limit,
                "seedRatioLimited": seed_ratio_limited,
                "speed-limit-down": speed_limit_down,
                "speed-limit-down-enabled": speed_limit_down_enabled,
                "speed-limit-up": speed_limit_up,
                "speed-limit-up-enabled": speed_limit_up_enabled,
                "start-added-torrents": start_added_torrents,
                "trash-original-torrent-files": trash_original_torrent_files,
                "utp-enabled": utp_enabled,
                "encryption": encryption,
                "script-torrent-added-filename": script_torrent_added_filename,
                "script-torrent-done-seeding-filename": script_torrent_done_seeding_filename,
                "script-torrent-done-seeding-enabled": script_torrent_done_seeding_enabled,
                "script-torrent-added-enabled": script_torrent_added_enabled,
                "default-trackers": "\n".join(default_trackers) if default_trackers is not None else None,
            }
        )

        args.update(kwargs)

        if args:
            self._request(RpcMethod.SessionSet, args, timeout=timeout)

    def blocklist_update(self, timeout: _Timeout | None = None) -> int | None:
        """Update block list. Returns the size of the block list."""
        result = self._request(RpcMethod.BlocklistUpdate, timeout=timeout)
        return result.get("blocklist-size")

    def port_test(self, timeout: _Timeout | None = None) -> bool | None:
        """
        Tests to see if your incoming peer port is accessible from the
        outside world.
        """
        result = self._request(RpcMethod.PortTest, timeout=timeout)
        return result.get("port-is-open")

    def free_space(self, path: str | pathlib.Path, timeout: _Timeout | None = None) -> int | None:
        """
        Get the amount of free space (in bytes) at the provided location.
        """
        self._rpc_version_warning(15)
        path = ensure_location_str(path)
        result: dict[str, Any] = self._request(RpcMethod.FreeSpace, {"path": path}, timeout=timeout)
        if result["path"] == path:
            return result["size-bytes"]
        return None

    def session_stats(self, timeout: _Timeout | None = None) -> SessionStats:
        """Get session statistics"""
        result = self._request(RpcMethod.SessionStats, timeout=timeout)
        return SessionStats(fields=result)

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
                "honorsSessionLimits": honors_session_limits,
                "speed-limit-down": speed_limit_down,
                "speed-limit-up-enabled": speed_limit_up_enabled,
                "speed-limit-up": speed_limit_up,
                "speed-limit-down-enabled": speed_limit_down_enabled,
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

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        self._http_session.close()


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
