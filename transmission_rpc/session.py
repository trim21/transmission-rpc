from __future__ import annotations

from typing import Literal

from transmission_rpc.types import Container


class Stats(Container):
    @property
    def uploaded_bytes(self) -> int:
        return self._get_field("uploaded_bytes")

    @property
    def downloaded_bytes(self) -> int:
        return self._get_field("downloaded_bytes")

    @property
    def files_added(self) -> int:
        return self._get_field("files_added")

    @property
    def session_count(self) -> int:
        return self._get_field("session_count")

    @property
    def seconds_active(self) -> int:
        return self._get_field("seconds_active")


class SessionStats(Container):
    # https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md
    # 42-session-statistics

    @property
    def active_torrent_count(self) -> int:
        return self._get_field("active_torrent_count")

    @property
    def download_speed(self) -> int:
        return self._get_field("download_speed")

    @property
    def paused_torrent_count(self) -> int:
        return self._get_field("paused_torrent_count")

    @property
    def torrent_count(self) -> int:
        return self._get_field("torrent_count")

    @property
    def upload_speed(self) -> int:
        return self._get_field("upload_speed")

    @property
    def cumulative_stats(self) -> Stats:
        return Stats(fields=self._get_field("cumulative_stats"))

    @property
    def current_stats(self) -> Stats:
        return Stats(fields=self._get_field("current_stats"))


class Units(Container):
    # 4 strings: KB/s, MB/s, GB/s, TB/s
    @property
    def speed_units(self) -> list[str]:
        return self._get_field("speed_units")

    # number of bytes in a KB (1000 for kB; 1024 for KiB)
    @property
    def speed_bytes(self) -> int:
        return self._get_field("speed_bytes")

    # 4 strings: KB/s, MB/s, GB/s, TB/s
    @property
    def size_units(self) -> list[str]:
        return self._get_field("size_units")

    # number of bytes in a KB (1000 for kB; 1024 for KiB)
    @property
    def size_bytes(self) -> int:
        return self._get_field("size_bytes")

    # 4 strings: KB/s, MB/s, GB/s, TB/s
    @property
    def memory_units(self) -> list[str]:
        return self._get_field("memory_units")

    # number of bytes in a KB (1000 for kB; 1024 for KiB)
    @property
    def memory_bytes(self) -> int:
        return self._get_field("memory_bytes")


class Session(Container):
    """
    Session is a class holding the session data for a Transmission daemon.

    Access the session field can be done through attributes.
    The attributes available are the same as the session arguments in the
    Transmission RPC specification, but with underscore instead of hyphen.


    You should use ``session.download_dir`` to get ``'download_dir'``.

    .. code-block:: python

        session = Client().get_session()

        current = session.download_dir

    https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md#41-session-arguments

    Warnings:
        setter on session's properties has been removed, please use :py:meth:`Client.set_session` instead
    """

    @property
    def alt_speed_down(self) -> int:
        """max global download speed (KBps)"""
        return self._get_field("alt_speed_down")

    @property
    def alt_speed_enabled(self) -> bool:
        # true means use the alt speeds
        return self._get_field("alt_speed_enabled")

    @property
    def alt_speed_time_begin(self) -> int:
        """when to turn on alt speeds (units: minutes after midnight)"""
        return self._get_field("alt_speed_time_begin")

    @property
    def alt_speed_time_day(self) -> int:
        """what day(s) to turn on alt speeds (look at tr_sched_day)"""
        return self._get_field("alt_speed_time_day")

    @property
    def alt_speed_time_enabled(self) -> bool:
        """true means the scheduled on/off times are used"""
        return self._get_field("alt_speed_time_enabled")

    @property
    def alt_speed_time_end(self) -> int:
        """when to turn off alt speeds (units: same)"""
        return self._get_field("alt_speed_time_end")

    @property
    def alt_speed_up(self) -> int:
        """max global upload speed (KBps)"""
        return self._get_field("alt_speed_up")

    @property
    def blocklist_enabled(self) -> bool:
        """true means enabled"""
        return self._get_field("blocklist_enabled")

    @property
    def blocklist_size(self) -> int:
        """int of rules in the blocklist"""
        return self._get_field("blocklist_size")

    @property
    def blocklist_url(self) -> str:
        """location of the blocklist to use for `blocklist-update`"""
        return self._get_field("blocklist_url")

    @property
    def cache_size_mib(self) -> int:
        """maximum size of the disk cache (MiB)"""
        return self._get_field("cache_size_mib")

    @property
    def config_dir(self) -> str:
        """location of transmission's configuration directory"""
        return self._get_field("config_dir")

    @property
    def dht_enabled(self) -> bool:
        """true means allow dht in public torrents"""
        return self._get_field("dht_enabled")

    @property
    def download_dir(self) -> str:
        """default path to download torrents"""
        return self._get_field("download_dir")

    @property
    def download_queue_enabled(self) -> bool:
        """if true, limit how many torrents can be downloaded at once"""
        return self._get_field("download_queue_enabled")

    @property
    def download_queue_size(self) -> int:
        """max int of torrents to download at once (see download-queue-enabled)"""
        return self._get_field("download_queue_size")

    @property
    def encryption(self) -> Literal["required", "preferred", "allowed", "tolerated"]:
        return self._get_field("encryption")

    @property
    def anti_brute_force_enabled(self) -> bool:
        return self._get_field("anti_brute_force_enabled")

    @property
    def idle_seeding_limit_enabled(self) -> bool:
        """true if the seeding inactivity limit is honored by default"""
        return self._get_field("idle_seeding_limit_enabled")

    @property
    def idle_seeding_limit(self) -> int:
        """torrents we're seeding will be stopped if they're idle for this long"""
        return self._get_field("idle_seeding_limit")

    @property
    def incomplete_dir_enabled(self) -> bool:
        """true means keep torrents in incomplete-dir until done"""
        return self._get_field("incomplete_dir_enabled")

    @property
    def incomplete_dir(self) -> str:
        """path for incomplete torrents, when enabled"""
        return self._get_field("incomplete_dir")

    @property
    def lpd_enabled(self) -> bool:
        """true means allow Local Peer Discovery in public torrents"""
        return self._get_field("lpd_enabled")

    @property
    def peer_limit_global(self) -> int:
        """maximum global int of peers"""
        return self._get_field("peer_limit_global")

    @property
    def peer_limit_per_torrent(self) -> int:
        """maximum global int of peers"""
        return self._get_field("peer_limit_per_torrent")

    @property
    def peer_port_random_on_start(self) -> bool:
        """true means pick a random peer port on launch"""
        return self._get_field("peer_port_random_on_start")

    @property
    def peer_port(self) -> int:
        """port int"""
        return self._get_field("peer_port")

    @property
    def pex_enabled(self) -> bool:
        """true means allow pex in public torrents"""
        return self._get_field("pex_enabled")

    @property
    def port_forwarding_enabled(self) -> bool:
        """true means ask upstream router to forward the configured peer port to transmission using UPnP or NAT-PMP"""
        return self._get_field("port_forwarding_enabled")

    @property
    def preferred_transports(self) -> list[str]:
        return self._get_field("preferred_transports")

    @property
    def queue_stalled_enabled(self) -> bool:
        """whether or not to consider idle torrents as stalled"""
        return self._get_field("queue_stalled_enabled")

    @property
    def queue_stalled_minutes(self) -> int:
        """torrents that are idle for N minutes aren't counted toward seed-queue-size or download-queue-size"""
        return self._get_field("queue_stalled_minutes")

    @property
    def rename_partial_files(self) -> bool:
        """true means append `.part` to incomplete files"""
        return self._get_field("rename_partial_files")

    @property
    def rpc_version_minimum(self) -> int:
        """the minimum RPC API version supported"""
        return self._get_field("rpc_version_minimum")

    @property
    def rpc_version(self) -> int:
        """the current RPC API version"""
        return self._get_field("rpc_version")

    @property
    def reqq(self) -> int:
        return self._get_field("reqq")

    @property
    def script_torrent_done_enabled(self) -> bool:
        """whether or not to call the `done` script"""
        return self._get_field("script_torrent_done_enabled")

    @property
    def script_torrent_done_filename(self) -> str:
        """filename of the script to run"""
        return self._get_field("script_torrent_done_filename")

    @property
    def seed_queue_enabled(self) -> bool:
        """if true, limit how many torrents can be uploaded at once"""
        return self._get_field("seed_queue_enabled")

    @property
    def seed_queue_size(self) -> int:
        """max int of torrents to uploaded at once (see seed-queue-enabled)"""
        return self._get_field("seed_queue_size")

    @property
    def seed_ratio_limit(self) -> float:
        """the default seed ratio for torrents to use"""
        return float(self._get_field("seed_ratio_limit"))

    @property
    def seed_ratio_limited(self) -> bool:
        """true if seedRatioLimit is honored by default"""
        return self._get_field("seed_ratio_limited")

    @property
    def sequential_download(self) -> bool:
        return self._get_field("sequential_download")

    @property
    def session_id(self) -> str:
        return self._get_field("session_id")

    @property
    def speed_limit_down_enabled(self) -> bool:
        """true means enabled"""
        return self._get_field("speed_limit_down_enabled")

    @property
    def speed_limit_down(self) -> int:
        """max global download speed (KBps)"""
        return self._get_field("speed_limit_down")

    @property
    def speed_limit_up_enabled(self) -> bool:
        """true means enabled"""
        return self._get_field("speed_limit_up_enabled")

    @property
    def speed_limit_up(self) -> int:
        """max global upload speed (KBps)"""
        return self._get_field("speed_limit_up")

    @property
    def start_added_torrents(self) -> bool:
        """true means added torrents will be started right away"""
        return self._get_field("start_added_torrents")

    @property
    def tcp_enabled(self) -> bool:
        return self._get_field("tcp_enabled")

    @property
    def trash_original_torrent_files(self) -> bool:
        """true means the .torrent file of added torrents will be deleted"""
        return self._get_field("trash_original_torrent_files")

    # see below
    @property
    def units(self) -> Units:
        return Units(fields=self._get_field("units"))

    @property
    def utp_enabled(self) -> bool:
        """true means allow utp"""
        return self._get_field("utp_enabled")

    @property
    def version(self) -> str:
        """long version str `$version ($revision)`"""
        return self._get_field("version")

    # Defensive check: handles legacy newline-separated strings and anticipates the JSON-RPC 2.0 shift to native arrays.
    @property
    def default_trackers(self) -> list[str] | None:
        """
        list of default trackers to use on public torrents
        new at rpc-version 17
        """
        trackers = self.get("default_trackers")
        if trackers:
            if isinstance(trackers, str):
                return trackers.split("\n")
            return trackers
        return None

    @property
    def rpc_version_semver(self) -> str | None:
        """
        the current RPC API version in a semver-compatible str
        new at rpc-version 17
        """
        return self.get("rpc_version_semver")

    @property
    def script_torrent_added_enabled(self) -> bool | None:
        """
        whether to call the `added` script
        new at rpc-version 17
        """
        return self.get("script_torrent_added_enabled")

    @property
    def script_torrent_added_filename(self) -> str | None:
        """
        filename of the script to run
        new at rpc-version 17
        """
        return self.get("script_torrent_added_filename")

    @property
    def script_torrent_done_seeding_enabled(self) -> bool | None:
        """
        whether to call the `seeding-done` script
        new at rpc-version 17
        """
        return self.get("script_torrent_done_seeding_enabled")

    @property
    def script_torrent_done_seeding_filename(self) -> str | None:
        """
        filename of the script to run
        new at rpc-version 17
        """
        return self.get("script_torrent_done_seeding_filename")
