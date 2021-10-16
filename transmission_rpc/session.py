# Copyright (c) 2018-2021 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.
from typing import Any, Dict, Union

from transmission_rpc.utils import _to_snake
from transmission_rpc.lib_types import _Base


class SessionCount(_Base):
    @property
    def downloaded_bytes(self) -> int:
        return self.__getattr__("downloaded_bytes")

    @property
    def files_added(self) -> int:
        return self.__getattr__("files_added")

    @property
    def seconds_active(self) -> int:
        return self.__getattr__("seconds_active")

    @property
    def session_count(self) -> int:
        return self.__getattr__("session_count")

    @property
    def uploaded_bytes(self) -> int:
        return self.__getattr__("uploaded_bytes")


class Stat(_Base):
    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self._fields["cumulative_stats"] = SessionCount(
            self._fields["cumulative_stats"]
        )
        self._fields["current_stats"] = SessionCount(self._fields["current_stats"])

    @property
    def cumulative_stats(self) -> SessionCount:
        return self.__getattr__("cumulative_stats")

    @property
    def current_stats(self) -> SessionCount:
        return self.__getattr__("current_stats")

    @property
    def active_torrent_count(self) -> int:
        return self.__getattr__("active_torrent_count")

    @property
    def download_speed(self) -> int:
        return self.__getattr__("download_speed")

    @property
    def paused_torrent_count(self) -> int:
        return self.__getattr__("paused_torrent_count")

    @property
    def torrent_count(self) -> int:
        return self.__getattr__("torrent_count")

    @property
    def upload_speed(self) -> int:
        return self.__getattr__("upload_speed")


class Session(_Base):
    """
    Session is a class holding the session data for a Transmission daemon.

    Access the session field can be done through attributes.
    The attributes available are the same as the session arguments in the
    Transmission RPC specification, but with underscore instead of hyphen.
    ``download-dir`` -> ``download_dir``.
    """

    def __str__(self) -> str:
        text = ""
        max_length = max(len(x) for x in self._fields.keys()) + 1
        for key, value in sorted(self._fields.items(), key=lambda x: x[0]):
            text += f"{key.ljust(max_length)}: {value!r}\n"
        return text

    def _update_fields(self, other: Union[Dict[str, Any], "Session"]) -> None:
        """
        Update the session data from a Transmission JSON-RPC arguments dictionary
        """
        if isinstance(other, dict):
            for key, value in other.items():
                self._fields[_to_snake(key)] = value
        elif isinstance(other, _Base):
            for key, value in other._fields.items():
                self._fields[key] = value
        else:
            raise ValueError("Cannot update with supplied data")

    def from_request(self, data: dict) -> None:
        """Update the session information."""
        self._update_fields(data)

    @property
    def download_dir(self) -> str:
        """default download location"""
        return self.__getattr__("download_dir")

    @property
    def version(self) -> str:
        return self.__getattr__("version")

    @property
    def rpc_version(self) -> int:
        return self.__getattr__("rpc_version")

    @property
    def peer_port(self) -> int:
        """Get the peer port."""
        return self.__getattr__("peer_port")

    @property
    def pex_enabled(self) -> bool:
        """Is peer exchange enabled"""
        return self.__getattr__("pex_enabled")

    @property
    def alt_speed_down(self) -> int:
        return self.__getattr__("alt_speed_down")

    @property
    def alt_speed_enabled(self) -> bool:
        return self.__getattr__("alt_speed_enabled")

    @property
    def alt_speed_time_begin(self) -> int:
        return self.__getattr__("alt_speed_time_begin")

    @property
    def alt_speed_time_day(self) -> int:
        return self.__getattr__("alt_speed_time_day")

    @property
    def alt_speed_time_enabled(self) -> bool:
        return self.__getattr__("alt_speed_time_enabled")

    @property
    def alt_speed_time_end(self) -> int:
        return self.__getattr__("alt_speed_time_end")

    @property
    def alt_speed_up(self) -> int:
        return self.__getattr__("alt_speed_up")

    @property
    def blocklist_enabled(self) -> bool:
        return self.__getattr__("blocklist_enabled")

    @property
    def blocklist_url(self) -> str:
        return self.__getattr__("blocklist_url")

    @property
    def cache_size_mb(self) -> int:
        return self.__getattr__("cache_size_mb")

    @property
    def dht_enabled(self) -> bool:
        return self.__getattr__("dht_enabled")

    @property
    def download_queue_enabled(self) -> bool:
        return self.__getattr__("download_queue_enabled")

    @property
    def download_queue_size(self) -> int:
        return self.__getattr__("download_queue_size")

    @property
    def encryption(self) -> str:
        return self.__getattr__("encryption")

    @property
    def idle_seeding_limit(self) -> int:
        return self.__getattr__("idle_seeding_limit")

    @property
    def idle_seeding_limit_enabled(self) -> bool:
        return self.__getattr__("idle_seeding_limit_enabled")

    @property
    def incomplete_dir(self) -> str:
        return self.__getattr__("incomplete_dir")

    @property
    def incomplete_dir_enabled(self) -> bool:
        return self.__getattr__("incomplete_dir_enabled")

    @property
    def lpd_enabled(self) -> bool:
        return self.__getattr__("lpd_enabled")

    @property
    def peer_limit_global(self) -> int:
        return self.__getattr__("peer_limit_global")

    @property
    def peer_limit_per_torrent(self) -> int:
        return self.__getattr__("peer_limit_per_torrent")

    @property
    def peer_port_random_on_start(self) -> bool:
        return self.__getattr__("peer_port_random_on_start")

    @property
    def port_forwarding_enabled(self) -> bool:
        return self.__getattr__("port_forwarding_enabled")

    @property
    def queue_stalled_enabled(self) -> bool:
        return self.__getattr__("queue_stalled_enabled")

    @property
    def queue_stalled_minutes(self) -> int:
        return self.__getattr__("queue_stalled_minutes")

    @property
    def rename_partial_files(self) -> bool:
        return self.__getattr__("rename_partial_files")

    @property
    def script_torrent_done_enabled(self) -> bool:
        return self.__getattr__("script_torrent_done_enabled")

    @property
    def script_torrent_done_filename(self) -> str:
        return self.__getattr__("script_torrent_done_filename")

    @property
    def seed_queue_enabled(self) -> bool:
        return self.__getattr__("seed_queue_enabled")

    @property
    def seed_queue_size(self) -> int:
        return self.__getattr__("seed_queue_size")

    @property
    def seed_ratio_limit(self) -> int:
        return self.__getattr__("seed_ratio_limit")

    @property
    def seed_ratio_limited(self) -> bool:
        return self.__getattr__("seed_ratio_limited")

    @property
    def speed_limit_down(self) -> int:
        return self.__getattr__("speed_limit_down")

    @property
    def speed_limit_down_enabled(self) -> bool:
        return self.__getattr__("speed_limit_down_enabled")

    @property
    def speed_limit_up(self) -> int:
        return self.__getattr__("speed_limit_up")

    @property
    def speed_limit_up_enabled(self) -> bool:
        return self.__getattr__("speed_limit_up_enabled")

    @property
    def start_added_torrents(self) -> bool:
        return self.__getattr__("start_added_torrents")

    @property
    def trash_original_torrent_files(self) -> bool:
        return self.__getattr__("trash_original_torrent_files")

    @property
    def utp_enabled(self) -> bool:
        return self.__getattr__("utp_enabled")
