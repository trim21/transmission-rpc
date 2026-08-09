# Copyright (c) 2018-2022 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.
from __future__ import annotations

import enum
import logging
from typing import NamedTuple

LOGGER = logging.getLogger("transmission-rpc")
LOGGER.setLevel(logging.ERROR)


class Priority(enum.IntEnum):
    Low = -1
    Normal = 0
    High = 1


class RatioLimitMode(enum.IntEnum):
    """torrent radio limit mode"""

    #: follow the global settings
    Global = 0
    #: override the global settings, seeding until a certain ratio
    Single = 1
    #: override the global settings, seeding regardless of ratio
    Unlimited = 2


class IdleMode(enum.IntEnum):
    """torrent idle mode"""

    #: follow the global settings
    Global = 0
    #: override the global settings, seeding until a certain idle time
    Single = 1
    #: override the global settings, seeding regardless of activity
    Unlimited = 2


class Args(NamedTuple):
    type: str
    added_version: int
    removed_version: int | None = None
    previous_argument_name: str | None = None
    next_argument_name: str | None = None
    description: str = ""

    def __repr__(self) -> str:
        return (
            f"Args({self.type!r},"
            f" {self.added_version!r},"
            f" {self.removed_version!r},"
            f" {self.previous_argument_name!r},"
            f" {self.next_argument_name!r},"
            f" {self.description!r})"
        )

    def __str__(self) -> str:
        return f"Args<type={self.type}, {self.added_version}, description={self.description!r})"


class Type:
    number = "number"
    string = "string"
    array = "array"
    boolean = "boolean"
    double = "double"
    object = "object"


TORRENT_GET_ARGS: dict[str, Args] = {
    "activity_date": Args(Type.number, 1, description="Last time of upload or download activity."),
    "added_date": Args(Type.number, 1, description="The date when this torrent was first added."),
    "availability": Args(
        Type.array,
        17,
        description="Number of connected peers that have each piece; -1 if the client has the piece.",
    ),
    "bandwidth_priority": Args(Type.number, 5, description="Bandwidth priority. Low (-1), Normal (0) or High (1)."),
    "comment": Args(Type.string, 1, description="Torrent comment."),
    "corrupt_ever": Args(Type.number, 1, description="Number of bytes of corrupt data downloaded."),
    "creator": Args(Type.string, 1, description="Torrent creator."),
    "date_created": Args(Type.number, 1, description="Torrent creation date."),
    "desired_available": Args(Type.number, 1, description="Number of bytes available and left to be downloaded."),
    "done_date": Args(Type.number, 1, description="The date when the torrent finished downloading."),
    "download_dir": Args(Type.string, 4, description="The directory path where the torrent is downloaded to."),
    "downloaded_ever": Args(Type.number, 1, description="Number of bytes of good data downloaded."),
    "download_limit": Args(Type.number, 1, None, None, None, "Download limit in Kbps."),
    "download_limit_mode": Args(
        Type.number, 1, 5, description="Download limit mode. 0 means global, 1 means single, 2 unlimited."
    ),
    "download_limited": Args(Type.boolean, 5, None, None, None, "Download limit is enabled"),
    "edit_date": Args(Type.number, 16),
    "error": Args(
        Type.number,
        1,
        description="Kind of error. 0 means OK, 1 means tracker warning, 2 means tracker error, 3 means local error.",
    ),
    "error_string": Args(Type.number, 1, None, None, None, "Error message."),
    "eta": Args(
        Type.number,
        1,
        description="Estimated number of seconds left when downloading or seeding. -1 means not available and -2 means unknown.",
    ),
    "eta_idle": Args(
        Type.number,
        15,
        description="Estimated number of seconds left until the idle time limit is reached. -1 means not available and -2 means unknown.",
    ),
    "files": Args(Type.array, 1, description="Array of file object containing key, bytes_completed, length and name."),
    "file_stats": Args(
        Type.array, 5, description="Array of file statistics containing bytes_completed, wanted and priority."
    ),
    "group": Args(Type.string, 17, description="The name of this torrent's bandwidth group"),
    "hash_string": Args(Type.string, 1, description="Hashstring unique for the torrent even between sessions."),
    "have_unchecked": Args(Type.number, 1, None, None, None, "Number of bytes of partial pieces."),
    "have_valid": Args(Type.number, 1, description="Number of bytes of checksum verified data."),
    "honors_session_limits": Args(Type.boolean, 5, description="True if session upload limits are honored"),
    "id": Args(Type.number, 1, None, None, None, "Session unique torrent id."),
    "is_finished": Args(Type.boolean, 9, description="True if the torrent is finished. Downloaded and seeded."),
    "is_private": Args(Type.boolean, 1, None, None, None, "True if the torrent is private."),
    "is_stalled": Args(Type.boolean, 14, description="True if the torrent has stalled (been idle for a long time)."),
    "labels": Args(Type.array, 16, None, None, None, "array of string labels"),
    "left_until_done": Args(Type.number, 1, description="Number of bytes left until the download is done."),
    "magnet_link": Args(Type.string, 7, None, None, None, "The magnet link for this torrent."),
    "manual_announce_time": Args(Type.number, 1, description="The time until you manually ask for more peers."),
    "max_connected_peers": Args(Type.number, 1, None, None, None, "Maximum of connected peers."),
    "metadata_percent_complete": Args(Type.double, 7, description="Download progress of metadata. 0.0 to 1.0."),
    "name": Args(Type.string, 1, None, None, None, "Torrent name."),
    "peer_limit": Args(Type.number, 5, None, None, None, "Maximum number of peers."),
    "peers": Args(Type.array, 2, None, None, None, "Array of peer objects."),
    "peers_connected": Args(Type.number, 1, None, None, None, "Number of peers we are connected to."),
    "peers_from": Args(Type.object, 1, description="Object containing download peers counts for different peer types."),
    "peers_getting_from_us": Args(Type.number, 1, description="Number of peers we are sending data to."),
    "peers_sending_to_us": Args(Type.number, 1, None, None, None, "Number of peers sending to us"),
    "percent_complete": Args(Type.double, 17),
    "percent_done": Args(Type.double, 5, description="Download progress of selected files. 0.0 to 1.0."),
    "pieces": Args(Type.string, 5, description="String with base64 encoded bitfield indicating finished pieces."),
    "piece_count": Args(Type.number, 1, None, None, None, "Number of pieces."),
    "piece_size": Args(Type.number, 1, None, None, None, "Number of bytes in a piece."),
    "priorities": Args(Type.array, 1, None, None, None, "Array of file priorities."),
    "primary_mime_type": Args(Type.string, 17),
    "queue_position": Args(Type.number, 14, None, None, None, "The queue position."),
    "rate_download": Args(Type.number, 1, None, None, None, "(B/s)"),
    "rate_upload": Args(Type.number, 1, None, None, None, "(B/s)"),
    "recheck_progress": Args(Type.double, 1, None, None, None, "Progress of recheck. 0.0 to 1.0."),
    "seconds_downloading": Args(Type.number, 15, None, None, None, ""),
    "seconds_seeding": Args(Type.number, 15, None, None, None, ""),
    "seed_idle_limit": Args(Type.number, 10, None, None, None, "Idle limit in minutes."),
    "seed_idle_mode": Args(Type.number, 10, description="Use global (0), torrent (1), or unlimited (2) limit."),
    "seed_ratio_limit": Args(Type.double, 5, None, None, None, "Seed ratio limit."),
    "seed_ratio_mode": Args(Type.number, 5, description="Use global (0), torrent (1), or unlimited (2) limit."),
    "sequential_download": Args(Type.boolean, 18, description="download torrent pieces sequentially"),
    "sequential_download_from_piece": Args(
        Type.number, 18, description="piece to start from when sequential download is enabled"
    ),
    "size_when_done": Args(Type.number, 1, description="Size of the torrent download in bytes."),
    "start_date": Args(Type.number, 1, description="The date when the torrent was last started."),
    "status": Args(Type.number, 1, None, None, None, "Current status, see source"),
    "trackers": Args(Type.array, 1, None, None, None, "Array of tracker objects."),
    "tracker_stats": Args(Type.object, 7, description="Array of object containing tracker statistics."),
    "total_size": Args(Type.number, 1, None, None, None, "Total size of the torrent in bytes"),
    "torrent_file": Args(Type.string, 5, None, None, None, "Path to .torrent file."),
    "uploaded_ever": Args(Type.number, 1, None, None, None, "Number of bytes uploaded, ever."),
    "upload_limit": Args(Type.number, 1, None, None, None, "Upload limit in Kbps"),
    "upload_limited": Args(Type.boolean, 5, None, None, None, "Upload limit enabled."),
    "upload_ratio": Args(Type.double, 1, None, None, None, "Seed ratio."),
    "wanted": Args(Type.array, 1, description="Array of booleans indicated wanted files."),
    "webseeds": Args(Type.array, 1, None, None, None, "Array of webseeds objects"),
    "webseeds_sending_to_us": Args(Type.number, 1, None, None, None, "Number of webseeds seeding to us."),
    "file_count": Args(Type.number, 17),
    "tracker_list": Args(
        Type.string,
        17,
        description="Announce URLs, one per line, with a blank line between tracker tiers.",
    ),
}


class RpcMethod(str, enum.Enum):
    SessionSet = "session-set"
    SessionGet = "session-get"
    SessionStats = "session-stats"
    SessionClose = "session-close"

    TorrentGet = "torrent-get"
    TorrentAdd = "torrent-add"
    TorrentSet = "torrent-set"
    TorrentRemove = "torrent-remove"

    TorrentStart = "torrent-start"
    TorrentStartNow = "torrent-start-now"  # added in 2.40
    TorrentStop = "torrent-stop"

    TorrentVerify = "torrent-verify"
    TorrentReannounce = "torrent-reannounce"

    TorrentSetLocation = "torrent-set-location"
    TorrentRenamePath = "torrent-rename-path"

    QueueMoveTop = "queue-move-top"
    QueueMoveBottom = "queue-move-bottom"
    QueueMoveUp = "queue-move-up"
    QueueMoveDown = "queue-move-down"

    GroupSet = "group-set"
    GroupGet = "group-get"

    FreeSpace = "free-space"

    PortTest = "port-test"

    BlocklistUpdate = "blocklist-update"


def get_torrent_arguments(rpc_version: int) -> list[str]:
    """
    Get torrent arguments for method in specified Transmission RPC version.
    """
    accessible: list[str] = []
    for argument, info in TORRENT_GET_ARGS.items():
        valid_version = True
        if rpc_version < info.added_version:
            valid_version = False
        if info.removed_version is not None and info.removed_version <= rpc_version:
            valid_version = False
        if valid_version:
            accessible.append(argument)
    return accessible
