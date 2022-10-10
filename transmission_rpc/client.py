# Copyright (c) 2018-2021 Trim21 <i@trim21.me>
# Copyright (c) 2020 littleya <me@littleya.com>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.
import os
import json
import time
import types
import string
import logging
import pathlib
import operator
import urllib.parse
from typing import (
    Any,
    Dict,
    List,
    Type,
    Tuple,
    Union,
    Literal,
    BinaryIO,
    Iterable,
    Optional,
)
from urllib.parse import quote, urljoin

import requests
import requests.auth
import requests.exceptions

from transmission_rpc.error import (
    TransmissionError,
    TransmissionAuthError,
    TransmissionConnectError,
    TransmissionTimeoutError,
)
from transmission_rpc.utils import _try_read_torrent, get_torrent_arguments
from transmission_rpc.session import Session
from transmission_rpc.torrent import Torrent
from transmission_rpc.constants import LOGGER, DEFAULT_TIMEOUT
from transmission_rpc.lib_types import Field, Group, _Timeout

valid_hash_char = string.digits + string.ascii_letters

_TorrentID = Union[int, str]
_TorrentIDs = Union[str, _TorrentID, List[_TorrentID], None]


def ensure_location_str(s: Union[str, pathlib.Path]) -> str:
    if isinstance(s, pathlib.Path):
        if s.is_absolute():
            return str(s)

        raise ValueError(
            "using relative `pathlib.Path` as remote path is not supported in v4.",
        )

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
                "logger must be instance of `logging.Logger`, default: logging.getLogger('transmission-rpc')"
            )
        self._query_timeout: _Timeout = timeout

        username = quote(username or "", safe="$-_.+!*'(),;&=", encoding="utf8") if username else ""
        password = ":" + quote(password or "", safe="$-_.+!*'(),;&=", encoding="utf8") if password else ""
        auth = f"{username}{password}@" if (username or password) else ""
        url = urllib.parse.urlunparse((protocol, f"{auth}{host}:{port}", urljoin(path, "rpc"), None, None, None))
        self.url = str(url)
        self._sequence = 0
        self.session: Session = Session(self)
        self.session_id = "0"
        self.server_version: Optional[Tuple[int, int, Optional[str]]] = None
        self.protocol_version: int = 17  # default 17
        self._http_session = requests.Session()
        self._http_session.trust_env = False
        self.get_session()
        self.torrent_get_arguments = get_torrent_arguments(self.rpc_version)

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
                    raise ValueError("element of timeout tuple can only be int of float")
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
                raise TransmissionError("too much request, try enable logger to see what happened")
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
                raise TransmissionTimeoutError("timeout when connection to transmission daemon") from e
            except requests.exceptions.ConnectionError as e:
                raise TransmissionConnectError(f"can't connect to transmission daemon: {str(e)}") from e

            self.session_id = r.headers.get("X-Transmission-Session-Id", "0")
            self.logger.debug(r.text)
            if r.status_code in {401, 403}:
                self.logger.debug(r.request.headers)
                raise TransmissionAuthError("transmission daemon require auth", original=r)
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
            self._update_session(data["arguments"])
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
        self.protocol_version = self.session.rpc_version

    @property
    def rpc_version(self) -> int:
        """
        Get the Transmission RPC version. Trying to deduct if the server don't have a version value.
        """
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
        labels: Iterable[str] = None,
        bandwidthPriority: int = None,
    ) -> Torrent:
        """
        Add torrent to transfers list. ``torrent`` can be:

        - ``http://``, ``https://`` or  ``magnet:`` URL
        - torrent file-like object in binary mode
        - bytes of torrent content
        - ``pathlib.Path`` for local torrent file, will be read and encoded as base64.

        Warnings
        --------
        base64 string or ``file://`` protocol URL are not supported in v4.

        Parameters
        ----------
        labels :
            Array of string labels.
            Add in rpc 17.
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
            If True, does not start the transfer when added.
        peer_limit:
            Maximum number of peers allowed.
        priority_high:
            A list of file id's that should have high priority.
        priority_low:
            A list of file id's that should have low priority.
        priority_normal:
            A list of file id's that should have normal priority.
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

        if labels is not None:
            self._rpc_version_warning(17)
            kwargs["labels"] = list(labels)

        torrent_data = _try_read_torrent(torrent)

        if torrent_data:
            kwargs["metainfo"] = torrent_data
        else:
            kwargs["filename"] = torrent

        return list(self._request("torrent-add", kwargs, timeout=timeout).values())[0]

    def remove_torrent(self, ids: _TorrentIDs, delete_data: bool = False, timeout: _Timeout = None) -> None:
        """
        remove torrent(s) with provided id(s). Local data is removed if
        delete_data is True, otherwise not.
        """
        self._request(
            "torrent-remove",
            {"delete-local-data": delete_data},
            ids,
            True,
            timeout=timeout,
        )

    def start_torrent(self, ids: _TorrentIDs, bypass_queue: bool = False, timeout: _Timeout = None) -> None:
        """Start torrent(s) with provided id(s)"""
        method = "torrent-start"
        if bypass_queue:
            method = "torrent-start-now"
        self._request(method, {}, ids, True, timeout=timeout)

    def start_all(self, bypass_queue: bool = False, timeout: _Timeout = None) -> None:
        """Start all torrents respecting the queue order"""
        method = "torrent-start"
        if bypass_queue:
            method = "torrent-start-now"
        torrent_list = sorted(self.get_torrents(), key=operator.attrgetter("queuePosition"))
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
        self._request("torrent-reannounce", {}, ids, True, timeout=timeout)

    def get_torrent(
        self,
        torrent_id: _TorrentID,
        arguments: Iterable[str] = None,
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
        arguments: Iterable[str] = None,
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
        return list(self._request("torrent-get", {"fields": arguments}, ids, timeout=timeout).values())

    def change_torrent(
        self,
        ids: _TorrentIDs,
        timeout: _Timeout = None,
        *,
        bandwidth_priority: int = None,
        download_limit: int = None,
        download_limited: bool = None,
        upload_limit: int = None,
        upload_limited: bool = None,
        files_unwanted: Iterable[int] = None,
        files_wanted: Iterable[int] = None,
        honors_session_limits: bool = None,
        location: str = None,
        peer_limit: int = None,
        priority_high: Iterable[int] = None,
        priority_low: Iterable[int] = None,
        priority_normal: Iterable[int] = None,
        queue_position: int = None,
        seed_idle_limit: int = None,
        seed_idle_mode: int = None,
        seed_ratio_limit: float = None,
        seed_ratio_mode: int = None,
        tracker_add: Iterable[str] = None,
        tracker_remove: Iterable[int] = None,
        tracker_replace: Iterable[Tuple[int, str]] = None,
        labels: Iterable[str] = None,
        group: str = None,
        tracker_list: Iterable[Iterable[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Change torrent parameters for the torrent(s) with the supplied id's.

        Parameters
        ----------
        ids
            torrent(s) to change.
        timeout
            requesst timeout.
        honors_session_limits
            true if session upload limits are honored.
        location
            new location of the torrent's content
        peer_limit
            maximum number of peers
        queue_position
            position of this torrent in its queue [0...n)
        files_wanted
            Array of file id to download.
        files_unwanted
            Array of file id to not download.
        download_limit
            maximum download speed (KBps)
        download_limited
            true if ``download_limit`` is honored
        upload_limit
            maximum upload speed (KBps)
        upload_limited
            true if ``upload_limit`` is honored
        bandwidth_priority
            Priority for this transfer.
        priority_high
            list of file id to set high download priority
        priority_low
            list of file id to set low download priority
        priority_normal
            list of file id to set normal download priority
        seed_ratio_limit
            Seed inactivity limit in minutes.
        seed_ratio_mode
            Which ratio to use.

            0 = Use session limit

            1 = Use transfer limit

            2 = Disable limit.
        seed_idle_limit
            torrent-level seeding ratio
        seed_idle_mode
            Seed inactivity mode.

            0 = Use session limit

            1 = Use transfer limit

            2 = Disable limit.
        tracker_add
            Array of string with announce URLs to add.
        tracker_remove
            Array of ids of trackers to remove.
        tracker_replace
            Array of (id, url) tuples where the announce URL should be replaced.
        labels
            Array of string labels.
            Add in rpc 16.
        group
            The name of this torrent's bandwidth group.
            Add in rpc 17.
        tracker_list
            A ``Iterable[Iterable[str]]``, each ``Iterable[str]`` for a tracker tier.
            Add in rpc 17.


        Warnings
        ----
        ``kwargs`` is for the future features not supported yet, it's not compatibility promising.

        it will be bypassed to request arguments.
        """

        args: Dict[str, Any] = {}

        if bandwidth_priority is not None:
            args["bandwidthPriority"] = bandwidth_priority

        if download_limit is not None:
            args["downloadLimit"] = download_limit
        if download_limited is not None:
            args["downloadLimited"] = download_limited
        if upload_limit is not None:
            args["uploadLimit"] = upload_limit
        if upload_limited is not None:
            args["uploadLimited"] = upload_limited
        if files_unwanted is not None:
            args["files-unwanted"] = list(files_unwanted)
        if files_wanted is not None:
            args["files-wanted"] = list(files_wanted)
        if honors_session_limits is not None:
            args["honorsSessionLimits"] = honors_session_limits
        if location is not None:
            args["location"] = location
        if peer_limit is not None:
            args["peer-limit"] = peer_limit
        if priority_high is not None:
            args["priority-high"] = list(priority_high)
        if priority_low is not None:
            args["priority-low"] = list(priority_low)
        if priority_normal is not None:
            args["priority-normal"] = list(priority_normal)
        if queue_position is not None:
            args["queuePosition"] = queue_position
        if seed_idle_limit is not None:
            args["seedIdleLimit"] = seed_idle_limit
        if seed_idle_mode is not None:
            args["seedIdleMode"] = seed_idle_mode
        if seed_ratio_limit is not None:
            args["seedRatioLimit"] = seed_ratio_limit
        if seed_ratio_mode is not None:
            args["seedRatioMode"] = seed_ratio_mode
        if tracker_add is not None:
            args["trackerAdd"] = tracker_add
        if tracker_remove is not None:
            args["trackerRemove"] = tracker_remove
        if tracker_replace is not None:
            args["trackerReplace"] = tracker_replace
        if labels is not None:
            self._rpc_version_warning(16)
            args["labels"] = list(labels)

        if tracker_list is not None:
            self._rpc_version_warning(17)
            args["trackerList"] = " ".join("\n".join(x) for x in tracker_list)

        if group is not None:
            self._rpc_version_warning(17)
            args["group"] = str(group)

        args.update(kwargs)

        if len(args) > 0:
            self._request("torrent-set", args, ids, True, timeout=timeout)
        else:
            ValueError("No arguments to set")

    def move_torrent_data(
        self,
        ids: _TorrentIDs,
        location: Union[str, pathlib.Path],
        timeout: _Timeout = None,
    ) -> None:
        """Move torrent data to the new location."""
        args = {"location": ensure_location_str(location), "move": True}
        self._request("torrent-set-location", args, ids, True, timeout=timeout)

    def locate_torrent_data(
        self,
        ids: _TorrentIDs,
        location: Union[str, pathlib.Path],
        timeout: _Timeout = None,
    ) -> None:
        """Locate torrent data at the provided location."""
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
        https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md#37-renaming-a-torrents-path

        This method can only be called on single torrent.
        """
        self._rpc_version_warning(15)
        torrent_id = _parse_torrent_id(torrent_id)
        name = name.strip()  # https://github.com/trim21/transmission-rpc/issues/185
        dirname = os.path.dirname(name)
        if len(dirname) > 0:
            raise ValueError("Target name cannot contain a path delimiter")
        result = self._request(
            "torrent-rename-path",
            {"path": ensure_location_str(location), "name": name},
            torrent_id,
            True,
            timeout=timeout,
        )
        return result["path"], result["name"]

    def queue_top(self, ids: _TorrentIDs, timeout: _Timeout = None) -> None:
        """Move transfer to the top of the queue:_Timeout."""
        self._request("queue-move-top", ids=ids, require_ids=True, timeout=timeout)

    def queue_bottom(self, ids: _TorrentIDs, timeout: _Timeout = None) -> None:
        """Move transfer to the bottom of the queue."""
        self._request("queue-move-bottom", ids=ids, require_ids=True, timeout=timeout)

    def queue_up(self, ids: _TorrentIDs, timeout: _Timeout = None) -> None:
        """Move transfer up in the queue."""
        self._request("queue-move-up", ids=ids, require_ids=True, timeout=timeout)

    def queue_down(self, ids: _TorrentIDs, timeout: _Timeout = None) -> None:
        """Move transfer down in the queue."""
        self._request("queue-move-down", ids=ids, require_ids=True, timeout=timeout)

    def get_session(self, timeout: _Timeout = None) -> Session:
        """
        Get session parameters. See the Session class for more information.
        """
        self._request("session-get", timeout=timeout)
        self._update_server_version()
        return self.session

    def set_session(
        self,
        timeout: _Timeout = None,
        *,
        alt_speed_down: int = None,
        alt_speed_enabled: bool = None,
        alt_speed_time_begin: int = None,
        alt_speed_time_day: int = None,
        alt_speed_time_enabled: bool = None,
        alt_speed_time_end: int = None,
        alt_speed_up: int = None,
        blocklist_enabled: bool = None,
        blocklist_url: str = None,
        cache_size_mb: int = None,
        dht_enabled: bool = None,
        download_dir: str = None,
        download_queue_enabled: bool = None,
        download_queue_size: int = None,
        encryption: Literal["required", "preferred", "tolerated"] = None,
        idle_seeding_limit: int = None,
        idle_seeding_limit_enabled: bool = None,
        incomplete_dir: str = None,
        incomplete_dir_enabled: bool = None,
        lpd_enabled: bool = None,
        peer_limit_global: int = None,
        peer_limit_per_torrent: int = None,
        peer_port: int = None,
        peer_port_random_on_start: bool = None,
        pex_enabled: bool = None,
        port_forwarding_enabled: bool = None,
        queue_stalled_enabled: bool = None,
        queue_stalled_minutes: int = None,
        rename_partial_files: bool = None,
        script_torrent_done_enabled: bool = None,
        script_torrent_done_filename: str = None,
        seed_queue_enabled: bool = None,
        seed_queue_size: int = None,
        seed_ratio_limit: int = None,
        seed_ratio_limited: bool = None,
        speed_limit_down: int = None,
        speed_limit_down_enabled: bool = None,
        speed_limit_up: int = None,
        speed_limit_up_enabled: bool = None,
        start_added_torrents: bool = None,
        trash_original_torrent_files: bool = None,
        utp_enabled: bool = None,
        script_torrent_done_seeding_filename: str = None,
        script_torrent_done_seeding_enabled: bool = None,
        script_torrent_added_enabled: bool = None,
        script_torrent_added_filename: str = None,
        **kwargs: Any,
    ) -> None:
        """
        Set session parameters.

        Parameters
        ----------
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

        Warnings
        ----
        ``kwargs`` is for the future features not supported yet, it's not compatibility promising.

        it will be bypassed to request arguments.
        """
        args: Dict[str, Any] = {}

        if alt_speed_down is not None:
            args["alt-speed-down"] = alt_speed_down
        if alt_speed_enabled is not None:
            args["alt-speed-enabled"] = alt_speed_enabled
        if alt_speed_time_begin is not None:
            args["alt-speed-time-begin"] = alt_speed_time_begin
        if alt_speed_time_day is not None:
            args["alt-speed-time-day"] = alt_speed_time_day
        if alt_speed_time_enabled is not None:
            args["alt-speed-time-enabled"] = alt_speed_time_enabled
        if alt_speed_time_end is not None:
            args["alt-speed-time-end"] = alt_speed_time_end
        if alt_speed_up is not None:
            args["alt-speed-up"] = alt_speed_up
        if blocklist_enabled is not None:
            args["blocklist-enabled"] = blocklist_enabled
        if blocklist_url is not None:
            args["blocklist-url"] = blocklist_url
        if cache_size_mb is not None:
            args["cache-size-mb"] = cache_size_mb
        if dht_enabled is not None:
            args["dht-enabled"] = dht_enabled
        if download_dir is not None:
            args["download-dir"] = download_dir
        if download_queue_enabled is not None:
            args["download-queue-enabled"] = download_queue_enabled
        if download_queue_size is not None:
            args["download-queue-size"] = download_queue_size
        if encryption is not None:
            if encryption not in ["required", "preferred", "tolerated"]:
                raise ValueError("Invalid encryption value")
            args["encryption"] = encryption
        if idle_seeding_limit_enabled is not None:
            args["idle-seeding-limit-enabled"] = idle_seeding_limit_enabled
        if idle_seeding_limit is not None:
            args["idle-seeding-limit"] = idle_seeding_limit
        if incomplete_dir is not None:
            args["incomplete-dir"] = incomplete_dir
        if incomplete_dir_enabled is not None:
            args["incomplete-dir-enabled"] = incomplete_dir_enabled
        if lpd_enabled is not None:
            args["lpd-enabled"] = lpd_enabled
        if peer_limit_global is not None:
            args["peer-limit-global"] = peer_limit_global
        if peer_limit_per_torrent is not None:
            args["peer-limit-per-torrent"] = peer_limit_per_torrent
        if peer_port_random_on_start is not None:
            args["peer-port-random-on-start"] = peer_port_random_on_start
        if peer_port is not None:
            args["peer-port"] = peer_port
        if pex_enabled is not None:
            args["pex-enabled"] = pex_enabled
        if port_forwarding_enabled is not None:
            args["port-forwarding-enabled"] = port_forwarding_enabled
        if queue_stalled_enabled is not None:
            args["queue-stalled-enabled"] = queue_stalled_enabled
        if queue_stalled_minutes is not None:
            args["queue-stalled-minutes"] = queue_stalled_minutes
        if rename_partial_files is not None:
            args["rename-partial-files"] = rename_partial_files
        if script_torrent_done_enabled is not None:
            args["script-torrent-done-enabled"] = script_torrent_done_enabled
        if script_torrent_done_filename is not None:
            args["script-torrent-done-filename"] = script_torrent_done_filename
        if seed_queue_enabled is not None:
            args["seed-queue-enabled"] = seed_queue_enabled
        if seed_queue_size is not None:
            args["seed-queue-size"] = seed_queue_size
        if seed_ratio_limit is not None:
            args["seedRatioLimit"] = seed_ratio_limit
        if seed_ratio_limited is not None:
            args["seedRatioLimited"] = seed_ratio_limited
        if speed_limit_down is not None:
            args["speed-limit-down"] = speed_limit_down
        if speed_limit_down_enabled is not None:
            args["speed-limit-down-enabled"] = speed_limit_down_enabled
        if speed_limit_up is not None:
            args["speed-limit-up"] = speed_limit_up
        if speed_limit_up_enabled is not None:
            args["speed-limit-up-enabled"] = speed_limit_up_enabled
        if start_added_torrents is not None:
            args["start-added-torrents"] = start_added_torrents
        if trash_original_torrent_files is not None:
            args["trash-original-torrent-files"] = trash_original_torrent_files
        if utp_enabled is not None:
            args["utp-enabled"] = utp_enabled

        if script_torrent_done_seeding_filename is not None:
            self._rpc_version_warning(17)
            args["script-torrent-done-seeding-filename"] = script_torrent_done_seeding_filename
        if script_torrent_done_seeding_enabled is not None:
            self._rpc_version_warning(17)
            args["script-torrent-done-seeding-enabled"] = script_torrent_done_seeding_enabled
        if script_torrent_added_enabled is not None:
            self._rpc_version_warning(17)
            args["script-torrent-added-enabled"] = script_torrent_added_enabled
        if script_torrent_added_filename is not None:
            self._rpc_version_warning(17)
            args["script-torrent-added-filename"] = script_torrent_added_filename

        args.update(kwargs)

        if len(args) > 0:
            self._request("session-set", args, timeout=timeout)

    def blocklist_update(self, timeout: _Timeout = None) -> Optional[int]:
        """Update block list. Returns the size of the block list."""
        result = self._request("blocklist-update", timeout=timeout)
        return result.get("blocklist-size")

    def port_test(self, timeout: _Timeout = None) -> Optional[bool]:
        """
        Tests to see if your incoming peer port is accessible from the
        outside world.
        """
        result = self._request("port-test", timeout=timeout)
        return result.get("port-is-open")

    def free_space(self, path: Union[str, pathlib.Path], timeout: _Timeout = None) -> Optional[int]:
        """
        Get the amount of free space (in bytes) at the provided location.
        """
        self._rpc_version_warning(15)
        path = ensure_location_str(path)
        result: Dict[str, Any] = self._request("free-space", {"path": path}, timeout=timeout)
        if result["path"] == path:
            return result["size-bytes"]
        return None

    def session_stats(self, timeout: _Timeout = None) -> Session:
        """Get session statistics"""
        self._request("session-stats", timeout=timeout)
        return self.session

    def set_group(
        self,
        name: str,
        *,
        timeout: _Timeout = None,
        honors_session_limits: bool = None,
        speed_limit_down: int = None,
        speed_limit_up_enabled: bool = None,
        speed_limit_up: int = None,
        speed_limit_down_enabled: bool = None,
    ) -> None:

        arguments: Dict[str, Any] = {"name": name}

        if honors_session_limits is not None:
            arguments["honorsSessionLimits"] = honors_session_limits

        if speed_limit_down is not None:
            arguments["speed-limit-down"] = speed_limit_down

        if speed_limit_up_enabled is not None:
            arguments["speed-limit-up-enabled"] = speed_limit_up_enabled

        if speed_limit_up is not None:
            arguments["speed-limit-up"] = speed_limit_up

        if speed_limit_down_enabled is not None:
            arguments["speed-limit-down-enabled"] = speed_limit_down_enabled

        self._request("group-set", arguments, timeout=timeout)

    def get_group(self, name: str, *, timeout: _Timeout = None) -> Optional[Group]:
        result: Dict[str, Any] = self._request("group-get", {"group": name}, timeout=timeout)

        if result["arguments"]["group"]:
            return Group.parse_obj(result["arguments"]["group"][0])
        return None

    def get_groups(self, name: List[str] = None, *, timeout: _Timeout = None) -> Dict[str, Group]:
        payload = {}
        if name is not None:
            payload = {"group": name}

        result: Dict[str, Any] = self._request("group-get", payload, timeout=timeout)

        return {x["name"]: Group.parse_obj(x) for x in result["arguments"]["group"]}

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, exc_type: Type[Exception], exc_val: Exception, exc_tb: types.TracebackType) -> None:
        self._http_session.close()
