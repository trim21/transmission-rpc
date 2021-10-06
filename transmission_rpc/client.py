# Copyright (c) 2018-2021 Trim21 <i@trim21.me>
# Copyright (c) 2020 littleya <me@littleya.com>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.
import os
import re
import enum
import json
import time
import types
import string
import logging
import pathlib
import operator
import warnings
import urllib.parse
from typing import (
    Any,
    Dict,
    List,
    Type,
    Tuple,
    Union,
    TypeVar,
    BinaryIO,
    Callable,
    Optional,
    Sequence,
)
from urllib.parse import quote, urljoin

import requests
import requests.auth
import requests.exceptions
from typing_extensions import Literal

from transmission_rpc.error import (
    TransmissionError,
    TransmissionAuthError,
    TransmissionConnectError,
    TransmissionTimeoutError,
    TransmissionVersionError,
)
from transmission_rpc.utils import (
    LOGGER,
    rpc_bool,
    get_arguments,
    make_rpc_name,
    _try_read_torrent,
    _rpc_version_check,
    argument_value_convert,
)
from transmission_rpc.session import Session
from transmission_rpc.torrent import Torrent
from transmission_rpc.constants import DEFAULT_TIMEOUT
from transmission_rpc.lib_types import File, Field, _Timeout

valid_hash_char = string.digits + string.ascii_letters

_TorrentID = Union[int, str]
_TorrentIDs = Union[str, _TorrentID, List[_TorrentID], None]


def ensure_location_str(s: Union[str, pathlib.Path]) -> str:
    if isinstance(s, pathlib.Path):
        if s.is_absolute():
            return str(s)

        warnings.warn(
            "`pathlib.Path` will be convert to absolute path automatically, "
            "please using a str or absolute Path to avoid unexpected path normalization\n"
            "This warning will become error in v4",
            DeprecationWarning,
        )
        return str(s.absolute())

    return str(s)


def _parse_torrent_id(raw_torrent_id: Union[int, str, Field]) -> Union[int, str]:
    if isinstance(raw_torrent_id, int):
        if raw_torrent_id >= 0:
            return raw_torrent_id
    elif isinstance(raw_torrent_id, str):
        if len(raw_torrent_id) != 40 or (set(raw_torrent_id) - set(valid_hash_char)):
            raise ValueError(f"torrent ids {raw_torrent_id} is not valid torrent id")
        return raw_torrent_id
    elif isinstance(raw_torrent_id, Field):
        return _parse_torrent_id(raw_torrent_id.value)
    raise ValueError(f"{raw_torrent_id} is not valid torrent id")


def _parse_torrent_ids(args: Any) -> Union[str, List[Union[str, int]]]:
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


class LimitMode(enum.IntEnum):
    use_session_limit_value = 0
    use_torrent_limit_value = 1
    disabled = 2


class Client:
    def __init__(
        self,
        *,
        protocol: Literal["http", "https"] = "http",
        username: str = None,
        password: str = None,
        host: str = "127.0.0.1",
        port: int = 9091,
        path: str = "/transmission/",
        timeout: Union[int, float] = DEFAULT_TIMEOUT,
        logger: logging.Logger = LOGGER,
    ):
        if isinstance(logger, logging.Logger):
            self.logger = logger
        else:
            raise TypeError(
                "logger must be instance of `logging.Logger`, "
                "default: logging.getLogger('transmission-rpc')"
            )
        self._query_timeout: _Timeout = timeout

        username = (
            quote(username or "", safe="$-_.+!*'(),;&=", encoding="utf8")
            if username
            else ""
        )
        password = (
            ":" + quote(password or "", safe="$-_.+!*'(),;&=", encoding="utf8")
            if password
            else ""
        )
        auth = f"{username}{password}@" if (username or password) else ""
        url = urllib.parse.urlunparse(
            (protocol, f"{auth}{host}:{port}", urljoin(path, "rpc"), None, None, None)
        )
        self.url = str(url)
        self._sequence = 0
        self.session: Session = Session(self)
        self.session_id = "0"
        self.server_version: Optional[Tuple[int, int, Optional[str]]] = None
        self.protocol_version: Optional[int] = None
        self._http_session = requests.Session()
        self._http_session.trust_env = False
        self.get_session()
        self.torrent_get_arguments = get_arguments("torrent-get", self.rpc_version)

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
                    raise ValueError(
                        "element of timeout tuple can only be int of float"
                    )
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
    def _http_header(self) -> Dict[str, str]:
        return {"x-transmission-session-id": self.session_id}

    def _http_query(self, query: dict, timeout: _Timeout = None) -> str:
        """
        Query Transmission through HTTP.
        """
        request_count = 0
        if timeout is None:
            timeout = self.timeout
        while True:
            if request_count >= 10:
                raise TransmissionError(
                    "too much request, try enable logger to see what happened"
                )
            self.logger.debug(
                {
                    "url": self.url,
                    "headers": self._http_header,
                    "data": query,
                    "timeout": timeout,
                }
            )
            request_count += 1
            try:
                r = self._http_session.post(
                    self.url,
                    headers=self._http_header,
                    json=query,
                    timeout=timeout,
                )
            except requests.exceptions.Timeout as e:
                raise TransmissionTimeoutError(
                    "timeout when connection to transmission daemon"
                ) from e
            except requests.exceptions.ConnectionError as e:
                raise TransmissionConnectError(
                    f"can't connect to transmission daemon: {str(e)}"
                ) from e

            self.session_id = r.headers.get("X-Transmission-Session-Id", "0")
            self.logger.debug(r.text)
            if r.status_code in {401, 403}:
                self.logger.debug(r.request.headers)
                raise TransmissionAuthError(
                    "transmission daemon require auth", original=r
                )
            if r.status_code != 409:
                return r.text

    def _request(
        self,
        method: str,
        arguments: Dict[str, Any] = None,
        ids: _TorrentIDs = None,
        require_ids: bool = False,
        timeout: _Timeout = None,
    ) -> dict:
        """
        Send json-rpc request to Transmission using http POST
        """
        if not isinstance(method, str):
            raise ValueError("request takes method as string")
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise ValueError("request takes arguments as dict")
        arguments = {key.replace("_", "-"): value for key, value in arguments.items()}
        ids = _parse_torrent_ids(ids)
        if len(ids) > 0:
            arguments["ids"] = ids
        elif require_ids:
            raise ValueError("request require ids")

        query = {"tag": self._sequence, "method": method, "arguments": arguments}

        self._sequence += 1
        start = time.time()
        http_data = self._http_query(query, timeout)
        elapsed = time.time() - start
        self.logger.info("http request took %.3f s", elapsed)

        try:
            data: dict = json.loads(http_data)
        except ValueError as error:
            self.logger.error("Error: %s", str(error))
            self.logger.error('Request: "%s"', query)
            self.logger.error('HTTP data: "%s"', http_data)
            raise ValueError from error

        self.logger.debug(json.dumps(data, indent=2))
        if "result" in data:
            if data["result"] != "success":
                raise TransmissionError(f'Query failed with result "{data["result"]}".')
        else:
            raise TransmissionError("Query failed without result.")

        results = {}
        if method == "torrent-get":
            for item in data["arguments"]["torrents"]:
                results[item["id"]] = Torrent(self, item)
                if self.protocol_version == 2 and "peers" not in item:
                    self.protocol_version = 1
        elif method == "torrent-add":
            item = None
            if "torrent-added" in data["arguments"]:
                item = data["arguments"]["torrent-added"]
            elif "torrent-duplicate" in data["arguments"]:
                item = data["arguments"]["torrent-duplicate"]
            if item:
                results[item["id"]] = Torrent(self, item)
            else:
                raise TransmissionError("Invalid torrent-add response.")
        elif method == "session-get":
            return data["arguments"]
        elif method == "session-stats":
            # older versions of T has the return data in "session-stats"
            if "session-stats" in data["arguments"]:
                self._update_session(data["arguments"]["session-stats"])
            else:
                self._update_session(data["arguments"])
        elif method in (
            "port-test",
            "blocklist-update",
            "free-space",
            "torrent-rename-path",
        ):
            results = data["arguments"]
        else:
            return data

        return results

    def _update_session(self, data: Dict[str, Any]) -> None:
        """
        Update session data.
        """
        if self.session:
            self.session._update(data)  # pylint: disable=W0212
        else:
            self.session = Session(self, data)

    def _update_server_version(self) -> None:
        """Decode the Transmission version string, if available."""
        if self.server_version is None:
            version_major = 2
            version_minor = 40
            version_change_set: Optional[str] = None
            version_parser = re.compile(r"(\d).(\d+) \((.*)\)")
            if hasattr(self.session, "version"):
                match = version_parser.match(self.session.version)
                if match:
                    version_major = int(match.group(1))
                    version_minor = int(match.group(2))
                    version_change_set = str(match.group(3))
            self.server_version = (version_major, version_minor, version_change_set)

    @property
    def rpc_version(self) -> int:
        """
        Get the Transmission RPC version. Trying to deduct if the server don't have a version value.
        """
        if self.protocol_version is None:
            # Ugly fix for 2.20 - 2.22 reporting rpc-version 11, but having new arguments
            if self.server_version and (
                self.server_version[0] == 2 and self.server_version[1] in [20, 21, 22]
            ):
                self.protocol_version = 12
            # Ugly fix for 2.12 reporting rpc-version 10, but having new arguments
            elif self.server_version and (
                self.server_version[0] == 2 and self.server_version[1] == 12
            ):
                self.protocol_version = 11
            elif "rpc_version" in self.session:
                self.protocol_version = self.session.rpc_version
            elif "version" in self.session:
                self.protocol_version = 3
            else:
                self.protocol_version = 2
        if self.server_version and (
            self.server_version[0] <= 2 and self.server_version[1] < 30
        ):
            warnings.warn(
                "support for transmission version lower than 2.30 (rpc version 13) will be removed in the future",
                PendingDeprecationWarning,
            )
        return self.protocol_version

    def _rpc_version_warning(self, required_version: int) -> None:
        """
        Add a warning to the log if the Transmission RPC version is lower then the provided version.
        """
        if self.rpc_version < required_version:
            self.logger.warning(
                "Using feature not supported by server. RPC version for server %d, feature introduced in %d.",
                self.rpc_version,
                required_version,
            )

    def _rpc_version_exception(
        self, required_version: int, argument: str = None
    ) -> None:
        """
        Add a warning to the log if the Transmission RPC version is lower then the provided version.
        """
        if self.rpc_version < required_version:
            if argument:
                msg = (
                    f"Arguments '{argument}' is not available at rpc version {self.rpc_version},"
                    f" argument add in {required_version}"
                )
            else:
                msg = (
                    f"Using feature not supported by server. RPC version for server {self.rpc_version},"
                    f" feature introduced in {required_version:d}."
                )
            raise TransmissionVersionError(msg)

    def add_torrent(
        self,
        torrent: Union[BinaryIO, str, bytes, pathlib.Path],
        timeout: _Timeout = None,
        *,
        download_dir: str = None,
        files_unwanted: List[int] = None,
        files_wanted: List[int] = None,
        paused: bool = None,
        peer_limit: int = None,
        priority_high: List[int] = None,
        priority_low: List[int] = None,
        priority_normal: List[int] = None,
        cookies: str = None,
        bandwidthPriority: int = None,
    ) -> Torrent:
        """
        Add torrent to transfers list. ``torrent`` can be:

        - ``http://``, ``https://`` or  ``magnet:`` URL
        - torrent file-like object in binary mode
        - bytes of torrent content
        - ``pathlib.Path`` for local torrent file, will be read and encoded as base64.
        - str of base64 encoded torrent file content - **deprecated**
        - ``file://`` URL - **deprecated**

        .. NOTE::

            url starts with ``file://`` will be load by this package instead of transmission daemon

        :param torrent:
        :param download_dir: remote download location
        :param files_unwanted: A list of file id's that shouldn't be downloaded.
        :param files_wanted: A list of file id's that should be downloaded.
        :param paused: If True, does not start the transfer when added.
        :param peer_limit: Maximum number of peers allowed.
        :param priority_high: A list of file id's that should have high priority.
        :param priority_low: A list of file id's that should have low priority.
        :param priority_normal: A list of file id's that should have normal priority.
        :param bandwidthPriority: Priority for this transfer. (require rpc>=8)
        :param cookies: One or more HTTP cookie(s) (rpc>=13)
        :param timeout:
        :rtype: Torrent
        """
        if torrent is None:
            raise ValueError("add_torrent requires data or a URI.")

        kwargs: Dict[str, Any] = {}
        if download_dir is not None:
            kwargs["download-dir"] = download_dir

        if files_unwanted is not None:
            kwargs["files-unwanted"] = files_unwanted

        if files_wanted is not None:
            kwargs["files-wanted"] = files_wanted

        if paused is not None:
            kwargs["paused"] = paused

        if peer_limit is not None:
            kwargs["peer-limit"] = peer_limit

        if priority_high is not None:
            kwargs["priority-high"] = priority_high

        if priority_low is not None:
            kwargs["priority-low"] = priority_low

        if priority_normal is not None:
            kwargs["priority-normal"] = priority_normal

        if bandwidthPriority is not None:
            kwargs["bandwidthPriority"] = bandwidthPriority

        if cookies is not None:
            kwargs["cookies"] = cookies

        torrent_data = _try_read_torrent(torrent)

        if torrent_data:
            kwargs["metainfo"] = torrent_data
        else:
            kwargs["filename"] = torrent

        _rpc_version_check("torrent-add", kwargs, self.rpc_version)

        return list(self._request("torrent-add", kwargs, timeout=timeout).values())[0]

    def remove_torrent(
        self, ids: _TorrentIDs, delete_data: bool = False, timeout: _Timeout = None
    ) -> None:
        """
        remove torrent(s) with provided id(s). Local data is removed if
        delete_data is True, otherwise not.
        """
        self._rpc_version_warning(3)
        self._request(
            "torrent-remove",
            {"delete-local-data": rpc_bool(delete_data)},
            ids,
            True,
            timeout=timeout,
        )

    def start_torrent(
        self, ids: _TorrentIDs, bypass_queue: bool = False, timeout: _Timeout = None
    ) -> None:
        """Start torrent(s) with provided id(s)"""
        method = "torrent-start"
        if bypass_queue and self.rpc_version >= 14:
            method = "torrent-start-now"
        self._request(method, {}, ids, True, timeout=timeout)

    def start_all(self, bypass_queue: bool = False, timeout: _Timeout = None) -> None:
        """Start all torrents respecting the queue order"""
        torrent_list = self.get_torrents()
        method = "torrent-start"
        if self.rpc_version >= 14:
            if bypass_queue:
                method = "torrent-start-now"
            torrent_list = sorted(
                torrent_list, key=operator.attrgetter("queuePosition")
            )
        self._request(
            method,
            {},
            ids=[x.id for x in torrent_list],
            require_ids=True,
            timeout=timeout,
        )

    def stop_torrent(self, ids: _TorrentIDs, timeout: _Timeout = None) -> None:
        """stop torrent(s) with provided id(s)"""
        self._request("torrent-stop", {}, ids, True, timeout=timeout)

    def verify_torrent(self, ids: _TorrentIDs, timeout: _Timeout = None) -> None:
        """verify torrent(s) with provided id(s)"""
        self._request("torrent-verify", {}, ids, True, timeout=timeout)

    def reannounce_torrent(self, ids: _TorrentIDs, timeout: _Timeout = None) -> None:
        """Reannounce torrent(s) with provided id(s)"""
        self._rpc_version_warning(5)
        self._request("torrent-reannounce", {}, ids, True, timeout=timeout)

    def get_torrent(
        self,
        torrent_id: _TorrentID,
        arguments: Sequence[str] = None,
        timeout: _Timeout = None,
    ) -> Torrent:
        """
        Get information for torrent with provided id.
        ``arguments`` contains a list of field names to be returned, when None
        all fields are requested. See the Torrent class for more information.

        new argument ``format`` in rpc_version 16 is unnecessarily
        and this lib can't handle table response, So it's unsupported.

        Returns a Torrent object with the requested fields.
        """
        if not arguments:
            arguments = self.torrent_get_arguments
        torrent_id = _parse_torrent_id(torrent_id)
        if torrent_id is None:
            raise ValueError("Invalid id")
        result: Dict[Union[str, int], Torrent] = self._request(
            "torrent-get",
            {"fields": arguments},
            torrent_id,
            require_ids=True,
            timeout=timeout,
        )
        if torrent_id in result:
            return result[torrent_id]
        for torrent in result.values():
            if torrent.hashString == torrent_id:
                return torrent
        raise KeyError("Torrent not found in result")

    def get_torrents(
        self,
        ids: _TorrentIDs = None,
        arguments: Sequence[str] = None,
        timeout: _Timeout = None,
    ) -> List[Torrent]:
        """
        Get information for torrents with provided ids. For more information see ``get_torrent``.

        Returns a list of Torrent object.
        """
        if arguments:
            arguments = list(set(arguments) | {"id"})
        else:
            arguments = self.torrent_get_arguments
        return list(
            self._request(
                "torrent-get", {"fields": arguments}, ids, timeout=timeout
            ).values()
        )

    def get_files(
        self,
        ids: _TorrentIDs = None,
        timeout: _Timeout = None,
    ) -> Dict[int, List[File]]:
        """
        Get list of files for provided torrent id(s). If ids is empty,
        information for all torrents are fetched. This function returns a dictionary
        for each requested torrent id holding the information about the files.

        See more detail in :py:meth:`transmission_rpc.torrent.Torrent.files`

        .. code-block:: python

            {
                <torrent id>: [
                    <File 0>,
                    <File 1>,
                    ...
                ],
                ...
            }

        """
        fields = ["id", "name", "hashString", "files", "priorities", "wanted"]
        request_result: Dict[int, Torrent] = self._request(
            "torrent-get", {"fields": fields}, ids, timeout=timeout
        )
        result = {}
        for tid, torrent in request_result.items():
            result[tid] = torrent.files()
        return result

    def set_files(
        self, items: Dict[str, Dict[int, Dict[str, Any]]], timeout: _Timeout = None
    ) -> None:
        """
        Set file properties. Takes a dictionary with similar contents as the result
        of :py:meth:`transmission_rpc.client.Client.get_files`.

        .. code-block:: python

            {
                <torrent id>: {
                    <file id>: {
                        'priority': <priority ('high'|'normal'|'low')>,
                        'selected': <selected for download (True|False)>
                    },
                    ...
                },
                ...
            }

        """
        if not isinstance(items, dict):
            raise ValueError("Invalid file description")
        for tid, files in items.items():
            if not isinstance(files, dict):
                continue
            wanted = []
            unwanted = []
            high = []
            normal = []
            low = []
            for fid, file_desc in files.items():
                if not isinstance(file_desc, dict):
                    continue
                if "selected" in file_desc and file_desc["selected"]:
                    wanted.append(fid)
                else:
                    unwanted.append(fid)
                if "priority" in file_desc:
                    if file_desc["priority"] == "high":
                        high.append(fid)
                    elif file_desc["priority"] == "normal":
                        normal.append(fid)
                    elif file_desc["priority"] == "low":
                        low.append(fid)

            self.change_torrent(
                [tid],
                timeout=timeout,
                priority_high=high or None,
                priority_normal=normal or None,
                priority_low=low or None,
                files_wanted=wanted or None,
                files_unwanted=unwanted or None,
            )

    def change_torrent(
        self,
        ids: _TorrentIDs,
        timeout: _Timeout = None,
        *,
        # rpc >= 1
        location: str = None,
        files_wanted: List[int] = None,
        files_unwanted: List[int] = None,
        peer_limit: int = None,
        priority_low: List[int] = None,
        priority_normal: List[int] = None,
        priority_high: List[int] = None,
        # replaced in rpc 5
        speed_limit_down: int = None,
        speed_limit_down_enabled: bool = None,
        speed_limit_up: int = None,
        speed_limit_up_enabled: bool = None,
        # rpc >= 5
        honorsSessionLimits: bool = None,
        bandwidthPriority: int = None,
        downloadLimit: int = None,
        downloadLimited: bool = None,
        uploadLimit: int = None,
        uploadLimited: bool = None,
        seedIdleLimit: int = None,
        seedIdleMode: int = None,
        # rpc >= 10
        seedRatioLimit: Union[int, float] = None,
        seedRatioMode: int = None,
        trackerAdd: List[str] = None,
        trackerRemove: List[str] = None,
        trackerReplace: Tuple[int, str] = None,
        # rpc >= 14
        queuePosition: int = None,
        # rpc >= 16
        labels: List[str] = None,
    ) -> None:
        """
        Change torrent parameters for the torrent(s) with the supplied id's. The

        parameters are:

        ============================ ===== =============== =============================================================
        Argument                     RPC   Replaced by     Description
        ============================ ===== =============== =============================================================
        ``files_wanted``             1 -                   A list of file id's that should be downloaded.
        ``files_unwanted``           1 -                   A list of file id's that shouldn't be downloaded.
        ``location``                 1 -                   Local download location.
        ``peer_limit``               1 -                   Maximum number of peers
        ``priority_high``            1 -                   A list of file id's that should have high priority.
        ``priority_low``             1 -                   A list of file id's that should have normal priority.
        ``priority_normal``          1 -                   A list of file id's that should have low priority.
        ``speed_limit_down``         1 - 5 downloadLimit   Set the speed limit for download in Kib/s.
        ``speed_limit_down_enabled`` 1 - 5 downloadLimited Enable download speed limiter.
        ``speed_limit_up``           1 - 5 uploadLimit     Set the speed limit for upload in Kib/s.
        ``speed_limit_up_enabled``   1 - 5 uploadLimited   Enable upload speed limiter.
        ``seedRatioLimit``           5 -                   Seeding ratio.
        ``seedRatioMode``            5 -                   Which ratio to use.
                                                            0 = Use session limit,
                                                            1 = Use per-torrent seed radio limit,
                                                            2 = Disable limit.
        ``honorsSessionLimits``      5 -                   Enables or disables the transfer to honour the upload limit
                                                            set in the session.
        ``bandwidthPriority``        5 -                   Priority for this transfer.
        ``downloadLimit``            5 -                   Set the speed limit for download in Kib/s.
        ``downloadLimited``          5 -                   Enable download speed limiter.
        ``uploadLimit``              5 -                   Set the speed limit for upload in Kib/s.
        ``uploadLimited``            5 -                   Enable upload speed limiter.
        ``seedIdleLimit``            10 -                  Seed inactivity limit in minutes.
        ``seedIdleMode``             10 -                  Seed inactivity mode. 0 = Use session limit,
                                                            1 = Use transfer limit, 2 = Disable limit.
        ``trackerAdd``               10 -                  Array of string with announce URLs to add.
        ``trackerRemove``            10 -                  Array of ids of trackers to remove.
        ``trackerReplace``           10 -                  Array of (0-based index, url) tuples where the announce URL should be r.
        ``queuePosition``            14 -                  Position of this transfer in its queue.
        ``labels``                   16 -                  Array of string labels.
        ============================ ===== =============== =============================================================
        """

        kwargs: Dict[str, Any] = {}

        if files_wanted is not None:
            kwargs["files_wanted"] = list(files_wanted)
        if files_unwanted is not None:
            kwargs["files_unwanted"] = list(files_unwanted)
        if location is not None:
            kwargs["location"] = str(location)
        if peer_limit is not None:
            kwargs["peer_limit"] = int(peer_limit)
        if priority_high is not None:
            kwargs["priority_high"] = list(priority_high)
        if priority_low is not None:
            kwargs["priority_low"] = list(priority_low)
        if priority_normal is not None:
            kwargs["priority_normal"] = list(priority_normal)

        value, replaced = _arg_replace(
            speed_limit_down,
            downloadLimit,
            self.rpc_version,
            5,
            int,
            "speed_limit_down",
            "downloadLimit",
        )
        if value is not None:
            if replaced:
                kwargs["downloadLimit"] = value
            else:
                kwargs["speed_limit_down"] = value

        value, replaced = _arg_replace(
            speed_limit_up,
            uploadLimit,
            self.rpc_version,
            5,
            int,
            "speed_limit_up",
            "uploadLimit",
        )
        if value is not None:
            if replaced:
                kwargs["uploadLimit"] = value
            else:
                kwargs["speed_limit_up"] = value

        value, replaced, = _arg_replace(
            speed_limit_down_enabled,
            downloadLimited,
            self.rpc_version,
            5,
            bool,
            "speed_limit_down_enabled",
            "downloadLimited",
        )
        if value is not None:
            if replaced:
                kwargs["downloadLimited"] = value
            else:
                kwargs["speed_limit_down_enabled"] = value

        value, replaced, = _arg_replace(
            speed_limit_up_enabled,
            uploadLimited,
            self.rpc_version,
            5,
            bool,
            "speed_limit_up_enabled",
            "uploadLimited",
        )
        if value is not None:
            if replaced:
                kwargs["uploadLimited"] = value
            else:
                kwargs["speed_limit_up_enabled"] = value

        # rpc 5
        if seedRatioLimit is not None:
            self._rpc_version_exception(5, "seedRatioLimit")
            kwargs["seedRatioLimit"] = seedRatioLimit
        if seedRatioMode is not None:
            self._rpc_version_exception(5, "seedRatioMode")
            kwargs["seedRatioMode"] = int(seedRatioMode)
        if honorsSessionLimits is not None:
            self._rpc_version_exception(5, "honorsSessionLimits")
            kwargs["honorsSessionLimits"] = bool(honorsSessionLimits)
        if bandwidthPriority is not None:
            self._rpc_version_exception(5, "bandwidthPriority")
            kwargs["bandwidthPriority"] = int(bandwidthPriority)

        # rpc 10
        if seedIdleLimit is not None:
            self._rpc_version_exception(10, "seedIdleLimit")
            kwargs["seedIdleLimit"] = int(seedIdleLimit)
        if seedIdleMode is not None:
            self._rpc_version_exception(10, "seedIdleMode")
            kwargs["seedIdleMode"] = int(seedIdleMode)
        if trackerAdd is not None:
            self._rpc_version_exception(10, "trackerAdd")
            kwargs["trackerAdd"] = list(trackerAdd)
        if trackerRemove is not None:
            self._rpc_version_exception(10, "trackerRemove")
            kwargs["trackerRemove"] = list(trackerRemove)
        if trackerReplace is not None:
            self._rpc_version_exception(10, "trackerReplace")
            index, torrent = trackerReplace
            kwargs["trackerReplace"] = (int(index), str(torrent))

        # rpc 14
        if queuePosition is not None:
            self._rpc_version_exception(14, "queuePosition")
            kwargs["queuePosition"] = int(queuePosition)

        # rpc 16
        if labels is not None:
            self._rpc_version_exception(16, "labels")
            kwargs["labels"] = list(labels)

        if kwargs:
            self._request("torrent-set", kwargs, ids, True, timeout=timeout)
        else:
            raise ValueError("No arguments to set")

    def move_torrent_data(
        self,
        ids: _TorrentIDs,
        location: Union[str, pathlib.Path],
        timeout: _Timeout = None,
    ) -> None:
        """Move torrent data to the new location."""
        self._rpc_version_warning(6)
        args = {"location": ensure_location_str(location), "move": True}
        self._request("torrent-set-location", args, ids, True, timeout=timeout)

    def locate_torrent_data(
        self,
        ids: _TorrentIDs,
        location: Union[str, pathlib.Path],
        timeout: _Timeout = None,
    ) -> None:
        """Locate torrent data at the provided location."""
        self._rpc_version_warning(6)
        args = {"location": ensure_location_str(location), "move": False}
        self._request("torrent-set-location", args, ids, True, timeout=timeout)

    def rename_torrent_path(
        self,
        torrent_id: _TorrentID,
        location: Union[str, pathlib.Path],
        name: str,
        timeout: _Timeout = None,
    ) -> Tuple[str, str]:
        """
        Rename directory and/or files for torrent.
        Remember to use get_torrent or get_torrents to update your file information.
        """
        self._rpc_version_warning(15)
        torrent_id = _parse_torrent_id(torrent_id)
        dirname = os.path.dirname(name)
        if len(dirname) > 0:
            raise ValueError("Target name cannot contain a path delimiter")
        args = {"path": ensure_location_str(location), "name": name}
        result = self._request(
            "torrent-rename-path", args, torrent_id, True, timeout=timeout
        )
        return result["path"], result["name"]

    def queue_top(self, ids: _TorrentIDs, timeout: _Timeout = None) -> None:
        """Move transfer to the top of the queue:_Timeout."""
        self._rpc_version_warning(14)
        self._request("queue-move-top", ids=ids, require_ids=True, timeout=timeout)

    def queue_bottom(self, ids: _TorrentIDs, timeout: _Timeout = None) -> None:
        """Move transfer to the bottom of the queue."""
        self._rpc_version_warning(14)
        self._request("queue-move-bottom", ids=ids, require_ids=True, timeout=timeout)

    def queue_up(self, ids: _TorrentIDs, timeout: _Timeout = None) -> None:
        """Move transfer up in the queue."""
        self._rpc_version_warning(14)
        self._request("queue-move-up", ids=ids, require_ids=True, timeout=timeout)

    def queue_down(self, ids: _TorrentIDs, timeout: _Timeout = None) -> None:
        """Move transfer down in the queue."""
        self._rpc_version_warning(14)
        self._request("queue-move-down", ids=ids, require_ids=True, timeout=timeout)

    def get_session(self, timeout: _Timeout = None) -> Session:
        """
        Get session parameters. See the Session class for more information.
        """
        self._update_session(self._request("session-get", timeout=timeout))
        self._update_server_version()
        return self.session

    def set_session(self, timeout: _Timeout = None, **kwargs: Any) -> None:
        """
        Set session parameters. The parameters are:

        ================================ ===== ================= ===========================================================
        Argument                         RPC   Replaced by       Description
        ================================ ===== ================= ===========================================================
        ``alt_speed_down``               5 -                     Alternate session download speed limit (in Kib/s).
        ``alt_speed_enabled``            5 -                     Enables alternate global download speed limiter.
        ``alt_speed_time_begin``         5 -                        Time when alternate speeds should be enabled.
                                                                    Minutes after midnight.
        ``alt_speed_time_day``           5 -                     Enables alternate speeds scheduling these days.
        ``alt_speed_time_enabled``       5 -                     Enables alternate speeds scheduling.
        ``alt_speed_time_end``           5 -                         Time when alternate speeds should be disabled.
                                                                     Minutes after midnight.
        ``alt_speed_up``                 5 -                     Alternate session upload speed limit (in Kib/s).
        ``blocklist_enabled``            5 -                     Enables the block list
        ``blocklist_url``                11 -                       Location of the block list.
                                                                    Updated with blocklist-update.
        ``cache_size_mb``                10 -                    The maximum size of the disk cache in MB
        ``dht_enabled``                  6 -                     Enables DHT.
        ``download_dir``                 1 -                     Set the session download directory.
        ``download_queue_enabled``       14 -                    Enables download queue.
        ``download_queue_size``          14 -                    Number of slots in the download queue.
        ``encryption``                   1 -                         Set the session encryption mode, one of ``required``,
                                                                     ``preferred`` or ``tolerated``.
        ``idle_seeding_limit``           10 -                    The default seed inactivity limit in minutes.
        ``idle_seeding_limit_enabled``   10 -                    Enables the default seed inactivity limit
        ``incomplete_dir``               7 -                     The path to the directory of incomplete transfer data.
        ``incomplete_dir_enabled``       7 -                         Enables the incomplete transfer data directory.

                                                                     Otherwise data for incomplete transfers are stored in
                                                                     the download target.
        ``lpd_enabled``                  9 -                     Enables local peer discovery for public torrents.
        ``peer_limit``                   1 - 5 peer-limit-global Maximum number of peers.
        ``peer_limit_global``            5 -                     Maximum number of peers.
        ``peer_limit_per_torrent``       5 -                     Maximum number of peers per transfer.
        ``peer_port``                    5 -                     Peer port.
        ``peer_port_random_on_start``    5 -                     Enables randomized peer port on start of Transmission.
        ``pex_allowed``                  1 - 5 pex-enabled       Allowing PEX in public torrents.
        ``pex_enabled``                  5 -                     Allowing PEX in public torrents.
        ``port``                         1 - 5 peer-port         Peer port.
        ``port_forwarding_enabled``      1 -                     Enables port forwarding.
        ``queue_stalled_enabled``        14 -                    Enable tracking of stalled transfers.
        ``queue_stalled_minutes``        14 -                    Number of minutes of idle that marks a transfer as stalled.
        ``rename_partial_files``         8 -                     Appends ".part" to incomplete files
        ``script_torrent_done_enabled``  9 -                     Whether or not to call the "done" script.
        ``script_torrent_done_filename`` 9 -                     Filename of the script to run when the transfer is done.
        ``seed_queue_enabled``           14 -                    Enables upload queue.
        ``seed_queue_size``              14 -                    Number of slots in the upload queue.
        ``seedRatioLimit``               5 -                     Seed ratio limit. 1.0 means 1:1 download and upload ratio.
        ``seedRatioLimited``             5 -                     Enables seed ration limit.
        ``speed_limit_down``             1 -                     Download speed limit (in Kib/s).
        ``speed_limit_down_enabled``     1 -                     Enables download speed limiting.
        ``speed_limit_up``               1 -                     Upload speed limit (in Kib/s).
        ``speed_limit_up_enabled``       1 -                     Enables upload speed limiting.
        ``start_added_torrents``         9 -                     Added torrents will be started right away.
        ``trash_original_torrent_files`` 9 -                     The .torrent file of added torrents will be deleted.
        ``utp_enabled``                  13 -                    Enables Micro Transport Protocol (UTP).
        ================================ ===== ================= ===========================================================

        .. NOTE::

           transmission_rpc will try to automatically fix argument errors.

        """
        args = {}
        for key, value in kwargs.items():
            if key == "encryption" and value not in [
                "required",
                "preferred",
                "tolerated",
            ]:
                raise ValueError("Invalid encryption value")
            argument = make_rpc_name(key)
            (arg, val) = argument_value_convert(
                "session-set", argument, value, self.rpc_version
            )
            args[arg] = val
        if len(args) > 0:
            self._request("session-set", args, timeout=timeout)

    def blocklist_update(self, timeout: _Timeout = None) -> Optional[int]:
        """Update block list. Returns the size of the block list."""
        self._rpc_version_warning(5)
        result = self._request("blocklist-update", timeout=timeout)
        return result.get("blocklist-size")

    def port_test(self, timeout: _Timeout = None) -> Optional[bool]:
        """
        Tests to see if your incoming peer port is accessible from the
        outside world.
        """
        self._rpc_version_warning(5)
        result = self._request("port-test", timeout=timeout)
        return result.get("port-is-open")

    def free_space(
        self, path: Union[str, pathlib.Path], timeout: _Timeout = None
    ) -> Optional[int]:
        """
        Get the amount of free space (in bytes) at the provided location.
        """
        self._rpc_version_warning(15)
        path = ensure_location_str(path)
        result: Dict[str, Any] = self._request(
            "free-space", {"path": path}, timeout=timeout
        )
        if result["path"] == path:
            return result["size-bytes"]
        return None

    def session_stats(self, timeout: _Timeout = None) -> Session:
        """Get session statistics"""
        self._request("session-stats", timeout=timeout)
        return self.session

    def __enter__(self) -> "Client":
        return self

    def __exit__(
        self,
        exc_type: Type[Exception],
        exc_val: Exception,
        exc_tb: types.TracebackType,
    ) -> None:
        self._http_session.close()


_T = TypeVar("_T")


def _arg_replace(
    old_value: Any,
    new_value: Any,
    rpc_version: int,
    replaced_rpc_version: int,
    convert: Callable[[Any], _T],
    old_name: str,
    new_name: str,
) -> Tuple[Optional[_T], bool]:
    v = None
    replaced = rpc_version >= replaced_rpc_version
    if old_value is not None and new_value is not None:
        if old_value != new_value:
            raise ValueError(
                f"old argument '{old_name}' are new argument '{new_name}' set to different value",
                old_value,
                new_value,
            )
        warnings.warn(
            f"don't use old argument '{old_name}' and new arguments '{new_name}' together"
        )
        v = convert(old_value)
    elif old_value is not None:
        if replaced:
            warnings.warn(
                f"you are using old argument '{old_name}', it's replaced by '{new_name}'"
            )
        v = convert(old_value)
    elif new_value is not None:
        if not replaced:
            warnings.warn(
                f"you are using argument '{new_name}', it's '{old_name}' in old transmission version"
            )
        v = convert(new_value)

    return v, replaced
