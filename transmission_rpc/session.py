from typing import List, Literal, Optional

from transmission_rpc.lib_types import Container


class Stats(Container):
    @property
    def uploaded_bytes(self) -> int:
        return self.fields["uploadedBytes"]

    @property
    def downloaded_bytes(self) -> int:
        return self.fields["downloadedBytes"]

    @property
    def files_added(self) -> int:
        return self.fields["filesAdded"]

    @property
    def session_count(self) -> int:
        return self.fields["sessionCount"]

    @property
    def seconds_active(self) -> int:
        return self.fields["secondsActive"]


class SessionStats(Container):
    # https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md
    # 42-session-statistics

    @property
    def active_torrent_count(self) -> int:
        return self.fields["activeTorrentCount"]

    @property
    def download_speed(self) -> int:
        return self.fields["downloadSpeed"]

    @property
    def paused_torrent_count(self) -> int:
        return self.fields["pausedTorrentCount"]

    @property
    def torrent_count(self) -> int:
        return self.fields["torrentCount"]

    @property
    def upload_speed(self) -> int:
        return self.fields["uploadSpeed"]

    @property
    def cumulative_stats(self) -> Stats:
        return Stats(fields=self.fields["cumulative-stats"])

    @property
    def current_stats(self) -> Stats:
        return Stats(fields=self.fields["current-stats"])


class Units(Container):
    # 4 strings: KB/s, MB/s, GB/s, TB/s
    @property
    def speed_units(self) -> List[str]:
        return self.fields["speed-units"]

    # number of bytes in a KB (1000 for kB; 1024 for KiB)
    @property
    def speed_bytes(self) -> int:
        return self.fields["speed-bytes"]

    # 4 strings: KB/s, MB/s, GB/s, TB/s
    @property
    def size_units(self) -> List[str]:
        return self.fields["size-units"]

    # number of bytes in a KB (1000 for kB; 1024 for KiB)
    @property
    def size_bytes(self) -> int:
        return self.fields["size-bytes"]

    # 4 strings: KB/s, MB/s, GB/s, TB/s
    @property
    def memory_units(self) -> List[str]:
        return self.fields["memory-units"]

    # number of bytes in a KB (1000 for kB; 1024 for KiB)
    @property
    def memory_bytes(self) -> int:
        return self.fields["memory-bytes"]


class Session(Container):
    """
        Session is a class holding the session data for a Transmission daemon.

        Access the session field can be done through attributes.
        The attributes available are the same as the session arguments in the
        Transmission RPC specification, but with underscore instead of hyphen.


        get ``'download-dir'`` with ``session.download_dir``.

        .. code-block:: python

            session = Client().get_session()

            current = session.download_dir


        Warnings
        --------
        setter on session's properties has been removed, please use ``Client().set_session()`` instead


        https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md
    #41-session-arguments
    """

    # max global download speed (KBps)
    @property
    def alt_speed_down(self) -> int:
        return self.fields["alt-speed-down"]

    # true means use the alt speeds
    @property
    def alt_speed_enabled(self) -> bool:
        return self.fields["alt-speed-enabled"]

    # when to turn on alt speeds (units: minutes after midnight)
    @property
    def alt_speed_time_begin(self) -> int:
        return self.fields["alt-speed-time-begin"]

    # what day(s) to turn on alt speeds (look at tr_sched_day)
    @property
    def alt_speed_time_day(self) -> int:
        return self.fields["alt-speed-time-day"]

    # true means the scheduled on/off times are used
    @property
    def alt_speed_time_enabled(self) -> bool:
        return self.fields["alt-speed-time-enabled"]

    # when to turn off alt speeds (units: same)
    @property
    def alt_speed_time_end(self) -> int:
        return self.fields["alt-speed-time-end"]

    # max global upload speed (KBps)
    @property
    def alt_speed_up(self) -> int:
        return self.fields["alt-speed-up"]

    # true means enabled
    @property
    def blocklist_enabled(self) -> bool:
        return self.fields["blocklist-enabled"]

    # int of rules in the blocklist
    @property
    def blocklist_size(self) -> int:
        return self.fields["blocklist-size"]

    # location of the blocklist to use for `blocklist-update`
    @property
    def blocklist_url(self) -> str:
        return self.fields["blocklist-url"]

    # maximum size of the disk cache (MB)
    @property
    def cache_size_mb(self) -> int:
        return self.fields["cache-size-mb"]

    # location of transmission's configuration directory
    @property
    def config_dir(self) -> str:
        return self.fields["config-dir"]

    # true means allow dht in public torrents
    @property
    def dht_enabled(self) -> bool:
        return self.fields["dht-enabled"]

    # default path to download torrents
    @property
    def download_dir(self) -> str:
        return self.fields["download-dir"]

    # **DEPRECATED** Use the `free-space` method instead.
    @property
    def download_dir_free_space(self) -> int:
        return self.fields["download-dir-free-space"]

    # if true, limit how many torrents can be downloaded at once
    @property
    def download_queue_enabled(self) -> bool:
        return self.fields["download-queue-enabled"]

    # max int of torrents to download at once (see download-queue-enabled)
    @property
    def download_queue_size(self) -> int:
        return self.fields["download-queue-size"]

    @property
    def encryption(self) -> Literal["required", "preferred", "tolerated"]:
        return self.fields["encryption"]

    # true if the seeding inactivity limit is honored by default
    @property
    def idle_seeding_limit_enabled(self) -> bool:
        return self.fields["idle-seeding-limit-enabled"]

    # torrents we're seeding will be stopped if they're idle for this long
    @property
    def idle_seeding_limit(self) -> int:
        return self.fields["idle-seeding-limit"]

    # true means keep torrents in incomplete-dir until done
    @property
    def incomplete_dir_enabled(self) -> bool:
        return self.fields["incomplete-dir-enabled"]

    # path for incomplete torrents, when enabled
    @property
    def incomplete_dir(self) -> str:
        return self.fields["incomplete-dir"]

    # true means allow Local Peer Discovery in public torrents
    @property
    def lpd_enabled(self) -> bool:
        return self.fields["lpd-enabled"]

    # maximum global int of peers
    @property
    def peer_limit_global(self) -> int:
        return self.fields["peer-limit-global"]

    # maximum global int of peers
    @property
    def peer_limit_per_torrent(self) -> int:
        return self.fields["peer-limit-per-torrent"]

    # true means pick a random peer port on launch
    @property
    def peer_port_random_on_start(self) -> bool:
        return self.fields["peer-port-random-on-start"]

    # port int
    @property
    def peer_port(self) -> int:
        return self.fields["peer-port"]

    # true means allow pex in public torrents
    @property
    def pex_enabled(self) -> bool:
        return self.fields["pex-enabled"]

    # true means ask upstream router to forward the configured peer port to transmission using UPnP or NAT-PMP
    @property
    def port_forwarding_enabled(self) -> bool:
        return self.fields["port-forwarding-enabled"]

    # whether or not to consider idle torrents as stalled
    @property
    def queue_stalled_enabled(self) -> bool:
        return self.fields["queue-stalled-enabled"]

    # torrents that are idle for N minutes aren't counted toward seed-queue-size or download-queue-size
    @property
    def queue_stalled_minutes(self) -> int:
        return self.fields["queue-stalled-minutes"]

    # true means append `.part` to incomplete files
    @property
    def rename_partial_files(self) -> bool:
        return self.fields["rename-partial-files"]

    # the minimum RPC API version supported
    @property
    def rpc_version_minimum(self) -> int:
        return self.fields["rpc-version-minimum"]

    # the current RPC API version
    @property
    def rpc_version(self) -> int:
        return self.fields["rpc-version"]

    # whether or not to call the `done` script
    @property
    def script_torrent_done_enabled(self) -> bool:
        return self.fields["script-torrent-done-enabled"]

    # filename of the script to run
    @property
    def script_torrent_done_filename(self) -> str:
        return self.fields["script-torrent-done-filename"]

    # if true, limit how many torrents can be uploaded at once
    @property
    def seed_queue_enabled(self) -> bool:
        return self.fields["seed-queue-enabled"]

    # max int of torrents to uploaded at once (see seed-queue-enabled)
    @property
    def seed_queue_size(self) -> int:
        return self.fields["seed-queue-size"]

    # the default seed ratio for torrents to use
    @property
    def seedRatioLimit(self) -> float:
        return self.fields["seedRatioLimit"]

    # true if seedRatioLimit is honored by default
    @property
    def seedRatioLimited(self) -> bool:
        return self.fields["seedRatioLimited"]

    # true means enabled
    @property
    def speed_limit_down_enabled(self) -> bool:
        return self.fields["speed-limit-down-enabled"]

    # max global download speed (KBps)
    @property
    def speed_limit_down(self) -> int:
        return self.fields["speed-limit-down"]

    # true means enabled
    @property
    def speed_limit_up_enabled(self) -> bool:
        return self.fields["speed-limit-up-enabled"]

    # max global upload speed (KBps)
    @property
    def speed_limit_up(self) -> int:
        return self.fields["speed-limit-up"]

    # true means added torrents will be started right away
    @property
    def start_added_torrents(self) -> bool:
        return self.fields["start-added-torrents"]

    # true means the .torrent file of added torrents will be deleted
    @property
    def trash_original_torrent_files(self) -> bool:
        return self.fields["trash-original-torrent-files"]

    # see below
    @property
    def units(self) -> Units:
        return self.fields["units"]

    # true means allow utp
    @property
    def utp_enabled(self) -> bool:
        return self.fields["utp-enabled"]

    # long version str `$version ($revision)`
    @property
    def version(self) -> str:
        return self.fields["version"]

    # list of default trackers to use on public torrents
    # new at rpc-version 17
    @property
    def default_trackers(self) -> Optional[list]:
        return self.get("default-trackers")

    # the current RPC API version in a semver-compatible str
    # new at rpc-version 17
    @property
    def rpc_version_semver(self) -> Optional[str]:
        return self.get("rpc-version-semver")

    # whether or not to call the `added` script
    # new at rpc-version 17
    @property
    def script_torrent_added_enabled(self) -> Optional[bool]:
        return self.get("script-torrent-added-enabled")

    # filename of the script to run
    # new at rpc-version 17
    @property
    def script_torrent_added_filename(self) -> Optional[str]:
        return self.get("script-torrent-added-filename")

    # whether or not to call the `seeding-done` script
    # new at rpc-version 17
    @property
    def script_torrent_done_seeding_enabled(self) -> Optional[bool]:
        return self.get("script-torrent-done-seeding-enabled")

    # filename of the script to run
    # new at rpc-version 17
    @property
    def script_torrent_done_seeding_filename(self) -> Optional[str]:
        return self.get("script-torrent-done-seeding-filename")
