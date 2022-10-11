# Copyright (c) 2018-2022 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.
import dataclasses
from typing import Literal

from transmission_rpc.ds import alias_metadata


@dataclasses.dataclass
class Stats:
    uploaded_bytes: int = dataclasses.field(metadata={alias_metadata: "uploadedBytes"})
    downloaded_bytes: int = dataclasses.field(metadata={alias_metadata: "downloadedBytes"})
    files_added: int = dataclasses.field(metadata={alias_metadata: "filesAdded"})
    session_count: int = dataclasses.field(metadata={alias_metadata: "sessionCount"})
    seconds_active: int = dataclasses.field(metadata={alias_metadata: "secondsActive"})


@dataclasses.dataclass
class SessionStats:
    # https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md#42-session-statistics

    active_torrent_count: int = dataclasses.field(metadata={alias_metadata: "activeTorrentCount"})
    download_speed: int = dataclasses.field(metadata={alias_metadata: "downloadSpeed"})
    paused_torrent_count: int = dataclasses.field(metadata={alias_metadata: "pausedTorrentCount"})
    torrent_count: int = dataclasses.field(metadata={alias_metadata: "torrentCount"})
    upload_speed: int = dataclasses.field(metadata={alias_metadata: "uploadSpeed"})
    cumulative_stats: Stats = dataclasses.field(metadata={alias_metadata: "cumulative-stats"})
    current_stats: Stats = dataclasses.field(metadata={alias_metadata: "current-stats"})


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
    """

    download_dir: str = dataclasses.field(metadata={alias_metadata: "download-dir"})
    version: str = dataclasses.field(metadata={alias_metadata: "version"})
    rpc_version: int = dataclasses.field(metadata={alias_metadata: "rpc-version"})
    peer_port: int = dataclasses.field(metadata={alias_metadata: "peer-port"})
    pex_enabled: bool = dataclasses.field(metadata={alias_metadata: "pex-enabled"})
    encryption: Literal["required", "preferred", "tolerated"] = dataclasses.field(
        metadata={alias_metadata: "encryption"}
    )
