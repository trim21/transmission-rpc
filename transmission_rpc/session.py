# Copyright (c) 2018-2022 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.

from typing import List, Literal, Optional
from dataclasses import field, dataclass

from transmission_rpc.ds import alias


@dataclass(frozen=True)
class Stats:
    uploaded_bytes: int = field(metadata={alias: "uploadedBytes"})
    downloaded_bytes: int = field(metadata={alias: "downloadedBytes"})
    files_added: int = field(metadata={alias: "filesAdded"})
    session_count: int = field(metadata={alias: "sessionCount"})
    seconds_active: int = field(metadata={alias: "secondsActive"})


@dataclass(frozen=True)
class SessionStats:
    # https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md
    # 42-session-statistics

    active_torrent_count: int = field(metadata={alias: "activeTorrentCount"})
    download_speed: int = field(metadata={alias: "downloadSpeed"})
    paused_torrent_count: int = field(metadata={alias: "pausedTorrentCount"})
    torrent_count: int = field(metadata={alias: "torrentCount"})
    upload_speed: int = field(metadata={alias: "uploadSpeed"})
    cumulative_stats: Stats = field(metadata={alias: "cumulative-stats"})
    current_stats: Stats = field(metadata={alias: "current-stats"})


@dataclass(frozen=True)
class Units:
    speed_units: List[str] = field(metadata={alias: "speed-units"})  # 4 strings: KB/s, MB/s, GB/s, TB/s
    speed_bytes: int = field(metadata={alias: "speed-bytes"})  # number of bytes in a KB (1000 for kB; 1024 for KiB)
    size_units: List[str] = field(metadata={alias: "size-units"})  # 4 strings: KB/s, MB/s, GB/s, TB/s
    size_bytes: int = field(metadata={alias: "size-bytes"})  # number of bytes in a KB (1000 for kB; 1024 for KiB)
    memory_units: List[str] = field(metadata={alias: "memory-units"})  # 4 strings: KB/s, MB/s, GB/s, TB/s
    memory_bytes: int = field(metadata={alias: "memory-bytes"})  # number of bytes in a KB (1000 for kB; 1024 for KiB)


@dataclass(frozen=True)
class Session:
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
    alt_speed_down: int = field(metadata={alias: "alt-speed-down"})

    # true means use the alt speeds
    alt_speed_enabled: bool = field(metadata={alias: "alt-speed-enabled"})

    # when to turn on alt speeds (units: minutes after midnight)
    alt_speed_time_begin: int = field(metadata={alias: "alt-speed-time-begin"})

    # what day(s) to turn on alt speeds (look at tr_sched_day)
    alt_speed_time_day: int = field(metadata={alias: "alt-speed-time-day"})

    # true means the scheduled on/off times are used
    alt_speed_time_enabled: bool = field(metadata={alias: "alt-speed-time-enabled"})

    # when to turn off alt speeds (units: same)
    alt_speed_time_end: int = field(metadata={alias: "alt-speed-time-end"})

    # max global upload speed (KBps)
    alt_speed_up: int = field(metadata={alias: "alt-speed-up"})

    # true means enabled
    blocklist_enabled: bool = field(metadata={alias: "blocklist-enabled"})

    # int of rules in the blocklist
    blocklist_size: int = field(metadata={alias: "blocklist-size"})

    # location of the blocklist to use for `blocklist-update`
    blocklist_url: str = field(metadata={alias: "blocklist-url"})

    # maximum size of the disk cache (MB)
    cache_size_mb: int = field(metadata={alias: "cache-size-mb"})

    # location of transmission's configuration directory
    config_dir: str = field(metadata={alias: "config-dir"})

    # true means allow dht in public torrents
    dht_enabled: bool = field(metadata={alias: "dht-enabled"})

    # default path to download torrents
    download_dir: str = field(metadata={alias: "download-dir"})

    # **DEPRECATED** Use the `free-space` method instead.
    download_dir_free_space: int = field(metadata={alias: "download-dir-free-space"})

    # if true, limit how many torrents can be downloaded at once
    download_queue_enabled: bool = field(metadata={alias: "download-queue-enabled"})

    # max int of torrents to download at once (see download-queue-enabled)
    download_queue_size: int = field(metadata={alias: "download-queue-size"})

    encryption: Literal["required", "preferred", "tolerated"] = field(metadata={alias: "encryption"})

    # true if the seeding inactivity limit is honored by default
    idle_seeding_limit_enabled: bool = field(metadata={alias: "idle-seeding-limit-enabled"})

    # torrents we're seeding will be stopped if they're idle for this long
    idle_seeding_limit: int = field(metadata={alias: "idle-seeding-limit"})

    # true means keep torrents in incomplete-dir until done
    incomplete_dir_enabled: bool = field(metadata={alias: "incomplete-dir-enabled"})

    # path for incomplete torrents, when enabled
    incomplete_dir: str = field(metadata={alias: "incomplete-dir"})

    # true means allow Local Peer Discovery in public torrents
    lpd_enabled: bool = field(metadata={alias: "lpd-enabled"})

    # maximum global int of peers
    peer_limit_global: int = field(metadata={alias: "peer-limit-global"})

    # maximum global int of peers
    peer_limit_per_torrent: int = field(metadata={alias: "peer-limit-per-torrent"})

    # true means pick a random peer port on launch
    peer_port_random_on_start: bool = field(metadata={alias: "peer-port-random-on-start"})

    # port int
    peer_port: int = field(metadata={alias: "peer-port"})

    # true means allow pex in public torrents
    pex_enabled: bool = field(metadata={alias: "pex-enabled"})

    # true means ask upstream router to forward the configured peer port to transmission using UPnP or NAT-PMP
    port_forwarding_enabled: bool = field(metadata={alias: "port-forwarding-enabled"})

    # whether or not to consider idle torrents as stalled
    queue_stalled_enabled: bool = field(metadata={alias: "queue-stalled-enabled"})

    # torrents that are idle for N minuets aren't counted toward seed-queue-size or download-queue-size
    queue_stalled_minutes: int = field(metadata={alias: "queue-stalled-minutes"})

    # true means append `.part` to incomplete files
    rename_partial_files: bool = field(metadata={alias: "rename-partial-files"})

    # the minimum RPC API version supported
    rpc_version_minimum: int = field(metadata={alias: "rpc-version-minimum"})

    # the current RPC API version
    rpc_version: int = field(metadata={alias: "rpc-version"})

    # whether or not to call the `done` script
    script_torrent_done_enabled: bool = field(metadata={alias: "script-torrent-done-enabled"})

    # filename of the script to run
    script_torrent_done_filename: str = field(metadata={alias: "script-torrent-done-filename"})

    # if true, limit how many torrents can be uploaded at once
    seed_queue_enabled: bool = field(metadata={alias: "seed-queue-enabled"})

    # max int of torrents to uploaded at once (see seed-queue-enabled)
    seed_queue_size: int = field(metadata={alias: "seed-queue-size"})

    # the default seed ratio for torrents to use
    seedRatioLimit: float = field(metadata={alias: "seedRatioLimit"})

    # true if seedRatioLimit is honored by default
    seedRatioLimited: bool = field(metadata={alias: "seedRatioLimited"})

    # true means enabled
    speed_limit_down_enabled: bool = field(metadata={alias: "speed-limit-down-enabled"})

    # max global download speed (KBps)
    speed_limit_down: int = field(metadata={alias: "speed-limit-down"})

    # true means enabled
    speed_limit_up_enabled: bool = field(metadata={alias: "speed-limit-up-enabled"})

    # max global upload speed (KBps)
    speed_limit_up: int = field(metadata={alias: "speed-limit-up"})

    # true means added torrents will be started right away
    start_added_torrents: bool = field(metadata={alias: "start-added-torrents"})

    # true means the .torrent file of added torrents will be deleted
    trash_original_torrent_files: bool = field(metadata={alias: "trash-original-torrent-files"})

    # see below
    units: Units = field(metadata={alias: "units"})

    # true means allow utp
    utp_enabled: bool = field(metadata={alias: "utp-enabled"})

    # long version str `$version ($revision)`
    version: str = field(metadata={alias: "version"})

    # list of default trackers to use on public torrents
    # new at rpc-version 17
    default_trackers: Optional[list] = field(default=None, metadata={alias: "default-trackers"})

    # the current RPC API version in a semver-compatible str
    # new at rpc-version 17
    rpc_version_semver: Optional[str] = field(default=None, metadata={alias: "rpc-version-semver"})

    # whether or not to call the `added` script
    # new at rpc-version 17
    script_torrent_added_enabled: Optional[bool] = field(default=None, metadata={alias: "script-torrent-added-enabled"})

    # filename of the script to run
    # new at rpc-version 17
    script_torrent_added_filename: Optional[str] = field(
        default=None, metadata={alias: "script-torrent-added-filename"}
    )

    # whether or not to call the `seeding-done` script
    # new at rpc-version 17
    script_torrent_done_seeding_enabled: Optional[bool] = field(
        default=None, metadata={alias: "script-torrent-done-seeding-enabled"}
    )

    # filename of the script to run
    # new at rpc-version 17
    script_torrent_done_seeding_filename: Optional[str] = field(
        default=None, metadata={alias: "script-torrent-done-seeding-filename"}
    )
