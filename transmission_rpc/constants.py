# Copyright (c) 2018-2021 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.
import logging
from typing import Dict, Optional, NamedTuple

LOGGER = logging.getLogger("transmission-rpc")
LOGGER.setLevel(logging.ERROR)


def mirror_dict(source: dict) -> dict:
    """
    Creates a dictionary with all values as keys and all keys as values.
    """
    source.update({value: key for key, value in source.items()})
    return source


DEFAULT_TIMEOUT = 30.0

TR_PRI_LOW = -1
TR_PRI_NORMAL = 0
TR_PRI_HIGH = 1

PRIORITY = mirror_dict({"low": TR_PRI_LOW, "normal": TR_PRI_NORMAL, "high": TR_PRI_HIGH})

TR_RATIOLIMIT_GLOBAL = 0  # follow the global settings
TR_RATIOLIMIT_SINGLE = 1  # override the global settings, seeding until a certain ratio
TR_RATIOLIMIT_UNLIMITED = 2  # override the global settings, seeding regardless of ratio

RATIO_LIMIT = mirror_dict(
    {
        "global": TR_RATIOLIMIT_GLOBAL,
        "single": TR_RATIOLIMIT_SINGLE,
        "unlimited": TR_RATIOLIMIT_UNLIMITED,
    }
)

TR_IDLELIMIT_GLOBAL = 0  # follow the global settings
TR_IDLELIMIT_SINGLE = 1  # override the global settings, seeding until a certain idle time
TR_IDLELIMIT_UNLIMITED = 2  # override the global settings, seeding regardless of activity

IDLE_LIMIT = mirror_dict(
    {
        "global": TR_RATIOLIMIT_GLOBAL,
        "single": TR_RATIOLIMIT_SINGLE,
        "unlimited": TR_RATIOLIMIT_UNLIMITED,
    }
)


class Args(NamedTuple):
    type: str
    added_version: int
    removed_version: Optional[int] = None
    previous_argument_name: Optional[str] = None
    next_argument_name: Optional[str] = None
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


trackerListDescription = "A Iterable[Iterable[str]] for a set of announce URLs, each inner list is for a tier"

TORRENT_GET_ARGS: Dict[str, Args] = {
    "activityDate": Args(Type.number, 1, description="Last time of upload or download activity."),
    "addedDate": Args(Type.number, 1, description="The date when this torrent was first added."),
    "bandwidthPriority": Args(Type.number, 5, description="Bandwidth priority. Low (-1), Normal (0) or High (1)."),
    "comment": Args(Type.string, 1, description="Torrent comment."),
    "corruptEver": Args(Type.number, 1, description="Number of bytes of corrupt data downloaded."),
    "creator": Args(Type.string, 1, description="Torrent creator."),
    "dateCreated": Args(Type.number, 1, description="Torrent creation date."),
    "desiredAvailable": Args(Type.number, 1, description="Number of bytes available and left to be downloaded."),
    "doneDate": Args(Type.number, 1, description="The date when the torrent finished downloading."),
    "downloadDir": Args(Type.string, 4, description="The directory path where the torrent is downloaded to."),
    "downloadedEver": Args(Type.number, 1, description="Number of bytes of good data downloaded."),
    "downloadLimit": Args(Type.number, 1, None, None, None, "Download limit in Kbps."),
    "downloadLimitMode": Args(
        Type.number, 1, 5, description="Download limit mode. 0 means global, 1 means single, 2 unlimited."
    ),
    "downloadLimited": Args(Type.boolean, 5, None, None, None, "Download limit is enabled"),
    "editDate": Args(Type.number, 16),
    "error": Args(
        Type.number,
        1,
        description="Kind of error. 0 means OK, 1 means tracker warning, 2 means tracker error, 3 means local error.",
    ),
    "errorString": Args(Type.number, 1, None, None, None, "Error message."),
    "eta": Args(
        Type.number,
        1,
        description="Estimated number of seconds left when downloading or seeding. -1 means not available and -2 means unknown.",
    ),
    "etaIdle": Args(
        Type.number,
        15,
        description="Estimated number of seconds left until the idle time limit is reached. -1 means not available and -2 means unknown.",
    ),
    "file-count": Args(Type.number, 17),
    "files": Args(Type.array, 1, description="Array of file object containing key, bytesCompleted, length and name."),
    "fileStats": Args(
        Type.array, 5, description="Away of file statistics containing bytesCompleted, wanted and priority."
    ),
    "group": Args(Type.string, 17, description="The name of this torrent's bandwidth group"),
    "hashString": Args(Type.string, 1, description="Hashstring unique for the torrent even between sessions."),
    "haveUnchecked": Args(Type.number, 1, None, None, None, "Number of bytes of partial pieces."),
    "haveValid": Args(Type.number, 1, description="Number of bytes of checksum verified data."),
    "honorsSessionLimits": Args(Type.boolean, 5, description="True if session upload limits are honored"),
    "id": Args(Type.number, 1, None, None, None, "Session unique torrent id."),
    "isFinished": Args(Type.boolean, 9, description="True if the torrent is finished. Downloaded and seeded."),
    "isPrivate": Args(Type.boolean, 1, None, None, None, "True if the torrent is private."),
    "isStalled": Args(Type.boolean, 14, description="True if the torrent has stalled (been idle for a long time)."),
    "labels": Args(Type.array, 16, None, None, None, "array of string labels"),
    "leftUntilDone": Args(Type.number, 1, description="Number of bytes left until the download is done."),
    "magnetLink": Args(Type.string, 7, None, None, None, "The magnet link for this torrent."),
    "manualAnnounceTime": Args(Type.number, 1, description="The time until you manually ask for more peers."),
    "maxConnectedPeers": Args(Type.number, 1, None, None, None, "Maximum of connected peers."),
    "metadataPercentComplete": Args(Type.number, 7, description="Download progress of metadata. 0.0 to 1.0."),
    "name": Args(Type.string, 1, None, None, None, "Torrent name."),
    "peer-limit": Args(Type.number, 5, None, None, None, "Maximum number of peers."),
    "peers": Args(Type.array, 2, None, None, None, "Array of peer objects."),
    "peersConnected": Args(Type.number, 1, None, None, None, "Number of peers we are connected to."),
    "peersFrom": Args(Type.object, 1, description="Object containing download peers counts for different peer types."),
    "peersGettingFromUs": Args(Type.number, 1, description="Number of peers we are sending data to."),
    "peersSendingToUs": Args(Type.number, 1, None, None, None, "Number of peers sending to us"),
    "percentComplete": Args(Type.double, 17),
    "percentDone": Args(Type.double, 5, description="Download progress of selected files. 0.0 to 1.0."),
    "pieces": Args(Type.string, 5, description="String with base64 encoded bitfield indicating finished pieces."),
    "pieceCount": Args(Type.number, 1, None, None, None, "Number of pieces."),
    "pieceSize": Args(Type.number, 1, None, None, None, "Number of bytes in a piece."),
    "priorities": Args(Type.array, 1, None, None, None, "Array of file priorities."),
    "primary-mime-type": Args(Type.string, 17),
    "queuePosition": Args(Type.number, 14, None, None, None, "The queue position."),
    "rateDownload": Args(Type.number, 1, None, None, None, "(B/s)"),
    "rateUpload": Args(Type.number, 1, None, None, None, "(B/s)"),
    "recheckProgress": Args(Type.double, 1, None, None, None, "Progress of recheck. 0.0 to 1.0."),
    "secondsDownloading": Args(Type.number, 15, None, None, None, ""),
    "secondsSeeding": Args(Type.number, 15, None, None, None, ""),
    "seedIdleLimit": Args(Type.number, 10, None, None, None, "Idle limit in minutes."),
    "seedIdleMode": Args(Type.number, 10, description="Use global (0), torrent (1), or unlimited (2) limit."),
    "seedRatioLimit": Args(Type.double, 5, None, None, None, "Seed ratio limit."),
    "seedRatioMode": Args(Type.number, 5, description="Use global (0), torrent (1), or unlimited (2) limit."),
    "sizeWhenDone": Args(Type.number, 1, description="Size of the torrent download in bytes."),
    "startDate": Args(Type.number, 1, description="The date when the torrent was last started."),
    "status": Args(Type.number, 1, None, None, None, "Current status, see source"),
    "trackers": Args(Type.array, 1, None, None, None, "Array of tracker objects."),
    "trackerList": Args(Type.array, 17, description=trackerListDescription),
    "trackerStats": Args(Type.object, 7, description="Array of object containing tracker statistics."),
    "totalSize": Args(Type.number, 1, None, None, None, "Total size of the torrent in bytes"),
    "torrentFile": Args(Type.string, 5, None, None, None, "Path to .torrent file."),
    "uploadedEver": Args(Type.number, 1, None, None, None, "Number of bytes uploaded, ever."),
    "uploadLimit": Args(Type.number, 1, None, None, None, "Upload limit in Kbps"),
    "uploadLimited": Args(Type.boolean, 5, None, None, None, "Upload limit enabled."),
    "uploadRatio": Args(Type.double, 1, None, None, None, "Seed ratio."),
    "wanted": Args(Type.array, 1, description="Array of booleans indicated wanted files."),
    "webseeds": Args(Type.array, 1, None, None, None, "Array of webseeds objects"),
    "webseedsSendingToUs": Args(Type.number, 1, None, None, None, "Number of webseeds seeding to us."),
}

TORRENT_SET_ARGS: Dict[str, Args] = {
    "bandwidthPriority": Args(Type.number, 5, None, None, None, "Priority for this transfer."),
    "downloadLimit": Args(Type.number, 5, None, "speed-limit-down", None, "Set the speed limit for download in Kib/s."),
    "downloadLimited": Args(Type.boolean, 5, None, "speed-limit-down-enabled", None, "Enable download speed limiter."),
    "files-unwanted": Args(Type.array, 1, description="A list of file id's that shouldn't be downloaded."),
    "files-wanted": Args(Type.array, 1, description="A list of file id's that should be downloaded."),
    "group": Args(Type.string, 17, description="The name of this torrent's bandwidth group"),
    "honorsSessionLimits": Args(Type.boolean, 5, description="true if session upload limits are honored"),
    # ids
    "labels": Args(Type.array, 16, None, None, None, "array of string labels"),
    "location": Args(Type.array, 1, None, None, None, "new location of the torrent's content"),
    "peer-limit": Args(Type.number, 1, None, None, None, "maximum number of peers"),
    "priority-high": Args(Type.array, 1, description="A list of file id's that should have high priority."),
    "priority-low": Args(Type.array, 1, description="A list of file id's that should have normal priority."),
    "priority-normal": Args(Type.array, 1, description="A list of file id's that should have low priority."),
    "queuePosition": Args(Type.number, 14, description="position of this torrent in its queue [0...n)"),
    "seedIdleLimit": Args(Type.number, 10, None, None, None, "Seed inactivity limit in minutes."),
    "seedIdleMode": Args(
        Type.number,
        10,
        description="Seed inactivity mode. 0 = Use session limit, 1 = Use transfer limit, 2 = Disable limit.",
    ),
    "seedRatioLimit": Args(Type.double, 5, None, None, None, "Seeding ratio."),
    "seedRatioMode": Args(
        Type.number,
        5,
        description="Which ratio to use. 0 = Use session limit, 1 = Use transfer limit, 2 = Disable limit.",
    ),
    "trackerList": Args(Type.array, 17, description=trackerListDescription),
    "trackerAdd": Args(Type.array, 10, removed_version=17, description="Array of string with announce URLs to add."),
    "trackerRemove": Args(Type.array, 10, removed_version=17, description="Array of ids of trackers to remove."),
    "trackerReplace": Args(
        Type.array, 10, 17, description="Array of (id, url) tuples where the announce URL should be replaced."
    ),
    "uploadLimit": Args(Type.number, 5, None, "speed-limit-up", None, "Set the speed limit for upload in Kib/s."),
    "uploadLimited": Args(Type.boolean, 5, None, "speed-limit-up-enabled", None, "Enable upload speed limiter."),
}

TORRENT_ADD_ARGS: Dict[str, Args] = {
    "cookies": Args(Type.string, 13, None, None, None, "One or more HTTP cookie(s)."),
    "download-dir": Args(Type.string, 1, description="The directory where the downloaded contents will be saved in."),
    "filename": Args(Type.string, 1, description="A file path or URL to a torrent file or a magnet link."),
    "labels": Args(Type.array, 17, description="A list of string labels"),
    # "metainfo": Args(Type.string, 1, description="The content of a torrent file, base64 encoded."),
    "paused": Args(Type.boolean, 1, description="If True, don't start the torrent"),
    "peer-limit": Args(Type.number, 1, description="Maximum number of peers allowed."),
    "bandwidthPriority": Args(Type.number, 8, None, None, None, "Priority for this transfer."),
    "files-wanted": Args(Type.array, 1, description="A list of file id's that should be downloaded."),
    "files-unwanted": Args(Type.array, 1, description="A list of file id's that shouldn't be downloaded."),
    "priority-high": Args(Type.array, 1, description="A list of file id's that should have high priority."),
    "priority-low": Args(Type.array, 1, description="A list of file id's that should have low priority."),
    "priority-normal": Args(Type.array, 1, description="A list of file id's that should have normal priority."),
}

SESSION_GET_ARGS = {
    "alt-speed-down": Args(Type.number, 5, description="Alternate session download speed limit (in Kib/s)."),
    "alt-speed-enabled": Args(
        Type.boolean, 5, description="True if alternate global download speed limiter is enabled."
    ),
    "alt-speed-time-begin": Args(
        Type.number, 5, description="Time when alternate speeds should be enabled. Minutes after midnight."
    ),
    "alt-speed-time-day": Args(Type.number, 5, description="Days alternate speeds scheduling is enabled."),
    "alt-speed-time-enabled": Args(Type.boolean, 5, description="True if alternate speeds scheduling is enabled."),
    "alt-speed-time-end": Args(
        Type.number, 5, description="Time when alternate speeds should be disabled. Minutes after midnight."
    ),
    "alt-speed-up": Args(Type.number, 5, description="Alternate session upload speed limit (in Kib/s)"),
    #
    "blocklist-enabled": Args(Type.boolean, 5, None, None, None, "True when blocklist is enabled."),
    "blocklist-size": Args(Type.number, 5, None, None, None, "Number of rules in the blocklist"),
    "blocklist-url": Args(Type.string, 11, description="Location of the block list. Updated with blocklist-update."),
    #
    "cache-size-mb": Args(Type.number, 10, description="The maximum size of the disk cache in MB"),
    "config-dir": Args(Type.string, 8, description="location of transmissions configuration directory"),
    #
    "default-trackers": Args(Type.array, 17, description="list of default trackers to use on public torrents"),
    "download-dir": Args(Type.string, 1, None, None, None, "The download directory."),
    "download-dir-free-space": Args(
        Type.number, 12, 17, None, "free-spaces", "Free space in the download directory, in bytes"
    ),
    "dht-enabled": Args(Type.boolean, 6, None, None, None, "True if DHT enabled."),
    "download-queue-size": Args(Type.number, 14, description="Number of slots in the download queue."),
    "download-queue-enabled": Args(Type.boolean, 14, description="True if the download queue is enabled."),
    #
    "encryption": Args(
        Type.string, 1, description="Encryption mode, one of ``required``, ``preferred`` or ``tolerated``."
    ),
    #
    "idle-seeding-limit-enabled": Args(Type.boolean, 10, description="True if the seed activity limit is enabled."),
    "idle-seeding-limit": Args(Type.number, 10, None, None, None, "Seed inactivity limit in minutes."),
    "incomplete-dir-enabled": Args(Type.boolean, 7, description="True if the incomplete dir is enabled."),
    "incomplete-dir": Args(
        Type.string, 7, description="The path to the directory for incomplete torrent transfer data."
    ),
    "lpd-enabled": Args(Type.boolean, 9, description="True if local peer discovery is enabled."),
    #
    "peer-limit-global": Args(Type.number, 5, None, "peer-limit", None, "Maximum number of peers."),
    "peer-limit-per-torrent": Args(Type.number, 5, description="Maximum number of peers per transfer."),
    "peer-port-random-on-start": Args(
        Type.boolean, 5, description="Enables randomized peer port on start of Transmission."
    ),
    "peer-port": Args(Type.number, 5, None, "port", None, "Peer port."),
    "pex-enabled": Args(Type.boolean, 5, None, "pex-allowed", None, "True if PEX is enabled."),
    "port": Args(Type.number, 1, 5, None, "peer-port", "Peer port."),
    "port-forwarding-enabled": Args(Type.boolean, 1, None, None, None, "True if port forwarding is enabled."),
    #
    "queue-stalled-enabled": Args(Type.boolean, 14, description="True if stalled tracking of transfers is enabled."),
    "queue-stalled-minutes": Args(
        Type.number, 14, description="Number of minutes of idle that marks a transfer as stalled."
    ),
    #
    "rename-partial-files": Args(Type.boolean, 8, description='True if ".part" is appended to incomplete files'),
    "rpc-version-minimum": Args(Type.number, 4, None, None, None, "Minimum accepted RPC API Version."),
    # TODO: number,string?
    "rpc-version-semver": Args(
        Type.string, 17, description="the current RPC API version in a semver-compatible string"
    ),
    "rpc-version": Args(Type.number, 4, None, None, None, "Transmission RPC API Version."),
    "script-torrent-added-filename": Args(Type.string, 17, description="whether or not to call the added script"),
    "script-torrent-added-enabled": Args(Type.boolean, 17, description="filename of the script to run"),
    "script-torrent-done-filename": Args(Type.string, 9, description="filename of the script to run"),
    "script-torrent-done-enabled": Args(Type.boolean, 9, None, None, None, "True if the done script is enabled."),
    "script-torrent-done-seeding-enabled": Args(
        Type.string, 17, description="whether or not to call the seeding-done script"
    ),
    "script-torrent-done-seeding-filename": Args(Type.string, 17, description="filename of the script to run"),
    "seed-queue-enabled": Args(Type.boolean, 14, None, None, None, "True if upload queue is enabled."),
    "seed-queue-size": Args(Type.number, 14, description="Number of slots in the upload queue."),
    "seedRatioLimit": Args(Type.double, 5, description="Seed ratio limit. 1.0 means 1:1 download and upload ratio."),
    "seedRatioLimited": Args(Type.boolean, 5, description="True if seed ration limit is enabled."),
    "speed-limit-down-enabled": Args(Type.boolean, 1, description="True if the download speed is limited."),
    "speed-limit-down": Args(Type.number, 1, None, None, None, "Download speed limit (in Kib/s)."),
    "speed-limit-up": Args(Type.number, 1, None, None, None, "Upload speed limit (in Kib/s)."),
    "speed-limit-up-enabled": Args(Type.boolean, 1, description="True if the upload speed is limited."),
    "start-added-torrents": Args(Type.boolean, 9, description="When true uploaded torrents will start right away."),
    "trash-original-torrent-files": Args(
        Type.boolean, 9, description="When true added .torrent files will be deleted."
    ),
    "units": Args(Type.object, 10, description="An object containing units for size and speed."),
    "version": Args(Type.string, 3, None, None, None, "Transmission version."),
    "utp-enabled": Args(Type.boolean, 13, description="True if Micro Transport Protocol (UTP) is enabled."),
    "fields": Args(Type.array, 16, None, None, None, "array of keys"),
    "session-id": Args(Type.string, 16, None, None, None, "session-id"),
}

SESSION_SET_ARGS = {
    "alt-speed-down": Args(Type.number, 5, description="Alternate session download speed limit (in Kib/s)."),
    "alt-speed-enabled": Args(
        Type.boolean, 5, description="True if alternate global download speed limiter is enabled."
    ),
    "alt-speed-time-begin": Args(
        Type.number, 5, description="Time when alternate speeds should be enabled. Minutes after midnight."
    ),
    "alt-speed-time-day": Args(Type.number, 5, description="Days alternate speeds scheduling is enabled."),
    "alt-speed-time-enabled": Args(Type.boolean, 5, description="True if alternate speeds scheduling is enabled."),
    "alt-speed-time-end": Args(
        Type.number, 5, description="Time when alternate speeds should be disabled. Minutes after midnight."
    ),
    "alt-speed-up": Args(Type.number, 5, description="Alternate session upload speed limit (in Kib/s)"),
    #
    "blocklist-enabled": Args(Type.boolean, 5, None, None, None, "True when blocklist is enabled."),
    "blocklist-url": Args(Type.string, 11, description="Location of the block list. Updated with blocklist-update."),
    #
    "cache-size-mb": Args(Type.number, 10, description="The maximum size of the disk cache in MB"),
    #
    "default-trackers": Args(Type.array, 17, description="list of default trackers to use on public torrents"),
    "download-dir": Args(Type.string, 1, None, None, None, "The download directory."),
    "download-dir-free-space": Args(
        Type.number, 12, 17, None, "free-spaces", "Free space in the download directory, in bytes"
    ),
    "dht-enabled": Args(Type.boolean, 6, None, None, None, "True if DHT enabled."),
    "download-queue-size": Args(Type.number, 14, description="Number of slots in the download queue."),
    "download-queue-enabled": Args(Type.boolean, 14, description="True if the download queue is enabled."),
    #
    "encryption": Args(
        Type.string, 1, description="Encryption mode, one of ``required``, ``preferred`` or ``tolerated``."
    ),
    #
    "idle-seeding-limit-enabled": Args(Type.boolean, 10, description="True if the seed activity limit is enabled."),
    "idle-seeding-limit": Args(Type.number, 10, None, None, None, "Seed inactivity limit in minutes."),
    "incomplete-dir-enabled": Args(Type.boolean, 7, description="True if the incomplete dir is enabled."),
    "incomplete-dir": Args(
        Type.string, 7, description="The path to the directory for incomplete torrent transfer data."
    ),
    "lpd-enabled": Args(Type.boolean, 9, description="True if local peer discovery is enabled."),
    #
    "peer-limit-global": Args(Type.number, 5, None, "peer-limit", None, "Maximum number of peers."),
    "peer-limit-per-torrent": Args(Type.number, 5, description="Maximum number of peers per transfer."),
    "peer-port-random-on-start": Args(
        Type.boolean, 5, description="Enables randomized peer port on start of Transmission."
    ),
    "peer-port": Args(Type.number, 5, None, "port", None, "Peer port."),
    "pex-enabled": Args(Type.boolean, 5, None, "pex-allowed", None, "True if PEX is enabled."),
    "port": Args(Type.number, 1, 5, None, "peer-port", "Peer port."),
    "port-forwarding-enabled": Args(Type.boolean, 1, None, None, None, "True if port forwarding is enabled."),
    #
    "queue-stalled-enabled": Args(Type.boolean, 14, description="True if stalled tracking of transfers is enabled."),
    "queue-stalled-minutes": Args(
        Type.number, 14, description="Number of minutes of idle that marks a transfer as stalled."
    ),
    #
    "rename-partial-files": Args(Type.boolean, 8, description='True if ".part" is appended to incomplete files'),
    "script-torrent-added-filename": Args(Type.string, 17, description="whether or not to call the added script"),
    "script-torrent-added-enabled": Args(Type.boolean, 17, description="filename of the script to run"),
    "script-torrent-done-filename": Args(Type.string, 9, description="filename of the script to run"),
    "script-torrent-done-enabled": Args(Type.boolean, 9, None, None, None, "True if the done script is enabled."),
    "script-torrent-done-seeding-enabled": Args(
        Type.string, 17, description="whether or not to call the seeding-done script"
    ),
    "script-torrent-done-seeding-filename": Args(Type.string, 17, description="filename of the script to run"),
    "seed-queue-enabled": Args(Type.boolean, 14, None, None, None, "True if upload queue is enabled."),
    "seed-queue-size": Args(Type.number, 14, description="Number of slots in the upload queue."),
    "seedRatioLimit": Args(Type.double, 5, description="Seed ratio limit. 1.0 means 1:1 download and upload ratio."),
    "seedRatioLimited": Args(Type.boolean, 5, description="True if seed ration limit is enabled."),
    "speed-limit-down-enabled": Args(Type.boolean, 1, description="True if the download speed is limited."),
    "speed-limit-down": Args(Type.number, 1, None, None, None, "Download speed limit (in Kib/s)."),
    "speed-limit-up": Args(Type.number, 1, None, None, None, "Upload speed limit (in Kib/s)."),
    "speed-limit-up-enabled": Args(Type.boolean, 1, description="True if the upload speed is limited."),
    "start-added-torrents": Args(Type.boolean, 9, description="When true uploaded torrents will start right away."),
    "trash-original-torrent-files": Args(
        Type.boolean, 9, description="When true added .torrent files will be deleted."
    ),
    "units": Args(Type.object, 10, description="An object containing units for size and speed."),
    "utp-enabled": Args(Type.boolean, 13, description="True if Micro Transport Protocol (UTP) is enabled."),
    "fields": Args(Type.array, 16, None, None, None, "array of keys"),
}


def get_args_by_method(method: str) -> Dict[str, Args]:
    if method == "torrent-add":
        return TORRENT_ADD_ARGS
    elif method == "torrent-get":
        return TORRENT_GET_ARGS
    elif method == "torrent-set":
        return TORRENT_SET_ARGS
    elif method == "session-get":
        return SESSION_GET_ARGS
    elif method == "session-set":
        return SESSION_SET_ARGS
    else:
        raise ValueError(f'Method "{method}" not supported')
